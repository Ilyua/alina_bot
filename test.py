import docx2pdf


outputFile = "document_test.pdf"
file = open(outputFile, "w")
file.close()
docx2pdf.convert(f'./tmp/894818505.docx', outputFile)