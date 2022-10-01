from flask import Flask, request, jsonify
import boto3
import gantry
import pandas as pd
import ast



app = Flask(__name__)

region_name = "us-west-2"

# Create a Secrets Manager client
session = boto3.session.Session()
secrets_manager = session.client(
    service_name='secretsmanager',
    region_name=region_name
)

rekognition = session.client("rekognition", "us-west-1")
s3_client = session.client("s3", "us-west-2")


MIN_CONFIDENCE = .9
HOTDOG_LABEL = "Hot Dog"
BUCKET_NAME = "hotdogapi"
secret_str = secrets_manager.get_secret_value(SecretId="gantry")["SecretString"]
secret_dict = ast.literal_eval(secret_str)
GANTRY_API_KEY = secret_dict["GANTRY_API_KEY"]


gantry.init(api_key=GANTRY_API_KEY)

APP_NAME = "Hot Dog API"


def _is_hot_dog(response):
    for label in response["Labels"]:
        if label["Name"] == HOTDOG_LABEL:
            return True
    return False

def save_image_to_s3(image_bytes, request_id):
    object_key = f"{request_id}.png"
    resp = s3_client.put_object(Body=image_bytes, Bucket=BUCKET_NAME, Key=object_key)

def log_to_gantry(request_id, response):
    s3_uri = f"s3://{BUCKET_NAME}/{request_id}.png"
    for label in response["Labels"]:
        inputs = pd.DataFrame([[s3_uri, request_id]],columns=["s3_uri", "request_id"])
        outputs = pd.DataFrame([[label["Name"], label["Confidence"]]], columns=["label", "confidence"])
        gantry.log_records(APP_NAME, inputs=inputs, outputs=outputs)

@app.route("/hotdog", methods=["POST"])
def hello_world():
    image = request.files["image"]
    image_bytes= image.read()
    response = rekognition.detect_labels(
        Image={
            "Bytes": image_bytes
        },
        MaxLabels=10,
        MinConfidence=MIN_CONFIDENCE
    )
    request_id = response["ResponseMetadata"]["RequestId"]
    save_image_to_s3(image_bytes, request_id)
    log_to_gantry(request_id, response)
    return jsonify({"is_hotdog": _is_hot_dog(response)})