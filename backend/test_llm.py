from services.llm_service import generate_response


response = generate_response(
    "Explain decorators in python"
)

print(response)