source .env

gcloud run deploy streamlit-app \
    --image europe-west2-docker.pkg.dev/govuk-ai-publishing/feedback-dashboard/app:latest \
    --region europe-west2 \
    --allow-unauthenticated \
    --min-instances 0 \
    --max-instances 2 \
    --ingress all \
    --port 8501 \
    --memory 4Gi \
    --cpu 4 \
    --service-account data-engineering@govuk-ai-publishing.iam.gserviceaccount.com \
    --set-env-vars PUBLISHING_PROJECT_ID=$PUBLISHING_PROJECT_ID,PUBLISHING_VIEW="\`$PUBLISHING_VIEW\`",QDRANT_HOST=$QDRANT_HOST,QDRANT_PORT=$QDRANT_PORT,COLLECTION_NAME=$COLLECTION_NAME,FILTER_OPTIONS_PATH=$FILTER_OPTIONS_PATH,HF_MODEL_NAME=$HF_MODEL_NAME,OPENAI_API_KEY=$OPENAI_API_KEY
