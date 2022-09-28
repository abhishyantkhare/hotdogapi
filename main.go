package main

import (
	"encoding/json"
	"net/http"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/rekognition"
)

const HOTDOG_LABEL = "Hot Dog"
const CONFIDENCE_THRESHOLD = .9

type HotdogRequestBody struct {
	Image []byte // Base64 encoding of the image
}

type HotdogResponse struct {
	IsHotdog bool `json:"isHotdog"`
}

func isHotdog(result *rekognition.DetectLabelsOutput) bool {
	if len(result.Labels) == 0 {
		return false
	}
	label := result.Labels[0]
	return (label.Name != nil && *label.Name == HOTDOG_LABEL) && (label.Confidence != nil && *label.Confidence >= CONFIDENCE_THRESHOLD)
}

func hotdog(w http.ResponseWriter, req *http.Request) {
	decoder := json.NewDecoder(req.Body)
    var hotdogRequestBody HotdogRequestBody
    err := decoder.Decode(&hotdogRequestBody)
    if err != nil {
        panic(err)
    }
	sess, err := session.NewSession(&aws.Config{
		Region: aws.String("us-west-1"),
	})
	if err != nil {
		panic(err)
	}
    svc := rekognition.New(sess)
	input := &rekognition.DetectLabelsInput{
		Image: &rekognition.Image{Bytes: hotdogRequestBody.Image},
		MaxLabels:     aws.Int64(1),
		MinConfidence: aws.Float64(90.000000),
	}	
	result, err := svc.DetectLabels(input)
	if err != nil {
		panic(err)
	}
	response := HotdogResponse{
		IsHotdog: isHotdog(result),
	}
	json.NewEncoder(w).Encode(response)
}

func main() {
	http.HandleFunc("/hotdog", hotdog)

	http.ListenAndServe(":80", nil)
}