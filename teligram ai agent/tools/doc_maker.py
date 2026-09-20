import os
import docx

class DocMakerTool:
    @staticmethod
    def create_document(prompt: str, router) -> str:
        content = router.execute_request(
            prompt=f"Generate the exact textual content for a Word Document based on this request: '{prompt}'. Do not include markdown formatting, just clear paragraphs and headings where appropriate.",
            system_prompt="You are a professional document writer. Provide high-quality content.",
            category="general"
        )
        if not content:
            return ""
        
        doc = docx.Document()
        for line in content.split("\n"):
            if line.strip():
                doc.add_paragraph(line.strip())
                
        file_path = os.path.join(os.getcwd(), "generated_document.docx")
        doc.save(file_path)
        return file_path
