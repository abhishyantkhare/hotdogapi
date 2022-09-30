from flask import Flask, request, jsonify
import boto3
import base64



app = Flask(__name__)

rekognition = boto3.client("rekognition", "us-west-1")

MIN_CONFIDENCE = .9
HOTDOG_LABEL = "Hot Dog"


def _is_hot_dog(response):
    if len(response["Labels"]) < 1:
        return False
    label = response["Labels"][0]
    return label["Name"] == HOTDOG_LABEL and label["Confidence"] > MIN_CONFIDENCE

@app.route("/hotdog", methods=["POST"])
def hello_world():
    image = request.files["image"]
    response = rekognition.detect_labels(
        Image={
            "Bytes": image.read()
        },
        MaxLabels=1,
        MinConfidence=MIN_CONFIDENCE
    )
    return jsonify({"is_hotdog": _is_hot_dog(response)})