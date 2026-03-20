from flask import Flask, request

from util.email import mail_init, get_mails

import json

import dataclasses, json

class EnhancedJSONEncoder(json.JSONEncoder):
        def default(self, o):
            if dataclasses.is_dataclass(o):
                return dataclasses.asdict(o)
            return super().default(o)



app = Flask(__name__)

imap = mail_init("imap.gmx.net")

@app.route("/mail/")
def hello_world():

    page = int(request.args.get("page", 1))
    batch_size = int(request.args.get("batchSize", 50))

    mails = get_mails(imap, batch_size, page)

    res = json.dumps({"mails": mails}, cls=EnhancedJSONEncoder)

    #print(res)

    return res