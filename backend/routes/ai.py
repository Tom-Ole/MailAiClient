from flask import Blueprint, jsonify, request

from util.clean import clean_email_html
from util.connections import get_imap, require_auth
from util.imap_client import get_mail_by_uid
import torch
import os

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

bp = Blueprint("ai", __name__, url_prefix="/ai")

device = "cuda" if torch.cuda.is_available() else "cpu"

model_path = os.path.join(os.getcwd(),"backend","safetensors", "billsum_model")

tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSeq2SeqLM.from_pretrained(model_path).to(device)

@bp.get("/summary/<uid>")
@require_auth
def get_mail(uid):
    """GET /ai/summary/<uid>?folder=INBOX"""
    folder = request.args.get("folder", "INBOX")
    imap = get_imap()
    mail = get_mail_by_uid(imap, uid=uid, folder=folder)

    if not mail:
        return jsonify({"error": "No mail found (ai.py)", "uid": uid, "folder": folder}), 404
    
    clean_body = clean_email_html(mail.body_html)

    inputs = tokenizer("summarize: " + clean_body, return_tensors="pt", truncation=True).to(device)

    outputs = model.generate(**inputs, max_new_tokens=128, num_beams=4)
    text = tokenizer.decode(outputs[0], skip_special_tokens=True)


    return jsonify({"summary": text, "uid": uid, "folder": folder})