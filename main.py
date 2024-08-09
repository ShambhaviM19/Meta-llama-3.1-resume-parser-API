import json
import re
from fastapi import FastAPI, UploadFile, File, HTTPException
import PyPDF2
import groq
from groq import Groq
from io import BytesIO

app = FastAPI()
client = groq.Groq(api_key="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")

def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def parse_resume(resume_text):
    prompt = f"""
    Parse the following resume and extract only the specified information in the exact JSON format provided. Do not include any fields that are not present in the resume.

    Resume text:
    {resume_text}

    Required JSON format:
    {{
      "Name": "",
      "Email": "",
      "Phone-Number": "",
      "Summary": "",
      "Current-Location": "",
      "Current-Company": "",
      "Skills": [],
      "Linkedin-Id": "",
      "Github-Id": "",
      "Total-Experience": 0,
      "Education": [
        {{
          "Degree": "",
          "Specialization": "",
          "Institute": "",
          "Start": 0,
          "End": 0
        }}
      ],
      "Education-Year": [],
      "Experiences": [
        {{
          "Company Name": "",
          "Designation": "",
          "Start": "",
          "End": "",
          "Description": ""
        }}
      ],
      "Projects": [
        {{
          "Project": "",
          "Project-Description": ""
        }}
      ],
      "Roles-Responsibility": [],
      "Certifications": []
    }}
    """

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="llama-3.1-70b-versatile",
        temperature=0
    )

    response = chat_completion.choices[0].message.content

    json_match = re.search(r'```\n(.*?)```', response, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return f"Error: Unable to parse JSON from extracted content. Extracted content: {json_str}"
    else:
        return f"Error: Unable to find JSON in response. Raw response: {response}"

@app.post("/parse-resume/")
async def parse_resume_endpoint(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDFs are allowed.")
    
    pdf_file = BytesIO(await file.read())
    resume_text = extract_text_from_pdf(pdf_file)
    
    parsed_resume = parse_resume(resume_text)
    
    if isinstance(parsed_resume, str) and parsed_resume.startswith("Error"):
        raise HTTPException(status_code=500, detail=parsed_resume)
    
    return parsed_resume

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
