from flask import Flask, request
from flask_restful import Api, Resource, reqparse, abort
from api import create_chatbot
from dotenv import load_dotenv
import os
from ecdsa import SigningKey

load_dotenv()
port = os.getenv('FLASK_RUN_PORT')

app = Flask(__name__)
api = Api(app)

@app.route('/')
def hello():
    return 'Hello, Karma Holder!'

if __name__ == '__main__':
    # 部署到云服务器上时，使用公共 IP 地址和端口 80
    app.run(debug=True,host='0.0.0.0', port=port)

# 请求验证
def validate_request(request):
   # 取出 Authorization 头中的 account
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        abort(401, message='Unauthorized')
    account = auth_header.split(' ')[-1]
    if not account:
        abort(401, message='Unauthorized')
    # 验证签名
    if request.headers.get('Content-Type') != 'application/json':
        abort(400, message='Bad Request')
    json_data = request.get_json()
    if not json_data:
        abort(400, message='Bad Request')
    if 'chatbotName' not in json_data:
        abort(400, message='Bad Request')
    signature = json_data.get('signature', '')
    if not signature:
        abort(400, message='Bad Request')
    data = {k: v for k, v in json_data.items() if k != 'signature'}
    data_str = json.dumps(data, sort_keys=True)
    vk = ecdsa.VerifyingKey.from_string(bytes.fromhex(account), curve=ecdsa.SECP256k1)
    try:
        vk.verify(bytes.fromhex(signature), data_str.encode('utf-8'))
    except ecdsa.BadSignatureError:
        abort(401, message='Unauthorized')
# Create 接口
class CreateChatbot(Resource):
    def post(self):
        validate_request(request)
        parser = reqparse.RequestParser()
        parser.add_argument('chatbotName', type=str, required=True)
        parser.add_argument('sourceText', type=str)
        args = parser.parse_args()
        chatbot_name = args['chatbotName']
        source_text = args.get('sourceText', '')
        # 调用 api.py 中的 create_chatbot 函数
        result = create_chatbot(chatbot_name, source_text)
        # 处理 POST 请求
        return {'message': f'Chatbot "{chatbot_name}" created with source text "{source_text}"'}

api.add_resource(CreateChatbot, '/api/v1/create-chatbot')