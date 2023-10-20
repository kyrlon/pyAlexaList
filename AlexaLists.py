import sysconfig
import json
import subprocess
from threading import Thread
import requests
import os, re, shutil, zipfile, tarfile
import platform, logging
from pathlib import Path
from flask import Flask, request, jsonify
from functools import wraps
from html.parser import HTMLParser
import timeit
from datetime import datetime
from copy import deepcopy



########################################
class AlexaAPI():
    def __init__(self):
        self._session = requests.Session()
        self.ngrok_server = Ngrok()
        self.server_running = False
        self.flask_server_endpoint = {"host": "127.0.0.1", "port": 5000}
        self.consent_token = self.requestConsentToken()
        self.updateHeader()
        self._endpoint_list_api = "https://api.amazonalexa.com/v2/householdlists/"

    def retryTokenOnExpire(func):
        @wraps(func)
        def wrapper(inst, *args, **kwargs):
            result = func(inst, *args, **kwargs)
            if isinstance(result, dict):
                if "Message" in result:
                    if result["Message"] == "Request is not authorized.":
                        inst.refreshToken()
                        result = func(inst, *args, **kwargs)
                        return result
                elif "items" in result and "ERROR 404" in result["items"]:
                    inst.refreshToken()
                    result = func(inst, *args, **kwargs)
                    return result
                else:
                    return result
            return result
        return wrapper

    @retryTokenOnExpire
    def createList(self):
        pass
    
    @retryTokenOnExpire
    def createListItem(self, list_id: str, item: dict):
        uri = self._endpoint_list_api + list_id + "/items"
        value = item["item_name"]
        status = "active" if not item["isDONE"] else "completed"
        request_body = {"value": value, "status": status}
        request_body = json.dumps(request_body)
        response = self._session.post(uri, data=request_body)
        content = response.content.decode()
        item_info = json.loads(content)
        return item_info
    
    @retryTokenOnExpire
    def getList(self, list_id):
        uri = self._endpoint_list_api + list_id + "/active"
        response = self._session.get(uri)
        active_content = response.content.decode()
        active_content = json.loads(active_content)
        if "Message" in active_content:
            active_content = {"items":["ERROR 404"]}

        uri = self._endpoint_list_api + list_id + "/completed"
        response = self._session.get(uri)
        completed_content = response.content.decode()
        completed_content = json.loads(completed_content)
        if "Message" in completed_content:
            completed_content = {"items":["ERROR 404"]}
        content = active_content.copy()
        content["items"].extend(completed_content["items"])
        return content

    def getListItem(self):
        pass
    
    @retryTokenOnExpire
    def getListMetadata(self):
        uri = self._endpoint_list_api
        response = self._session.get(uri)
        content = response.content.decode()
        content = json.loads(content)
        return content

    def updateList(self):
        pass
    
    @retryTokenOnExpire
    def updateListItem(self, list_id, item_id, item_name, version_num, status="completed"):
        uri = self._endpoint_list_api + list_id + "/items/" + item_id
        request_body = {
            "status": status,
            "value": item_name,
            "version": version_num
            }
        request_body = json.dumps(request_body)
        response = self._session.put(uri, data=request_body)
        content = response.content.decode()
        item_info = json.loads(content)
        return item_info

    def deleteList(self):
        pass
    
    @retryTokenOnExpire
    def deleteListItem(self, list_id, item_id):
        uri = self._endpoint_list_api + list_id + "/items/" + item_id      
        response = self._session.delete(uri)
        content = response.content.decode()
        if content:
            item_info = json.loads(content)
            return item_info
        return content

    def refreshToken(self):
        self.consent_token = self.requestConsentToken()
        self.updateHeader()


    def updateHeader(self):
        self._session.headers.update(
            {
                "Authorization": "Bearer " + self.consent_token,
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )

    def requestConsentToken(self):
        # Load client ID and Secret values
        with open("client_info.json", "r") as cred:
            client_info = json.load(cred)

        CLIENT_ID = client_info["Developer"]["clientID"]
        CLIENT_SECRET = client_info["Developer"]["clientSecret"]
        ALEXA_USER_ID = client_info["Developer"]["userID"]

        # Getting token for api requests
        HEADERS = {
            "X-Amzn-RequestId": "d917ceac-2245-11e2-a270-0bc161cb589d",
            "Content-Type": "application/json"
        }

        DATA = {"client_id": CLIENT_ID, "grant_type": "client_credentials",
                "client_secret": CLIENT_SECRET, "scope": "alexa:skill_messaging"}

        url = "https://api.amazon.com/auth/o2/token"

        DATA = json.dumps(DATA)
        response = requests.post(url, data=DATA, headers=HEADERS)
        info = json.loads(response.text)
        access_token = info["access_token"]

        HEADERS = {
            "Authorization": "Bearer " + access_token,
            "Content-Type": "application/json",
        }

        if not self.server_running:
            self.startTokenServer()
        API_URL = f"https://api.amazonalexa.com/v1/skillmessages/users/{ALEXA_USER_ID}"

        if not self.ngrok_server.up:
            self.ngrok_server.startProcess()
        ngrok_endpoint = self.ngrok_server.getUrl()

        URLL = ngrok_endpoint + "/send/accesstoken"
        a_data = {"data": {"endpoint": URLL}, "expiresAfterSeconds": 60}
        a_data = json.dumps(a_data)
        a_response = requests.post(API_URL, data=a_data, headers=HEADERS)
        consent_token = requests.get("http://127.0.0.1:5000/retrieve/accesstoken")
        consent_token = json.loads(consent_token.text)
        if "TOKENN" not in consent_token:
            self.ngrok_server.stopProcess()
            self.requestConsentToken()
        self.ngrok_server.stopProcess()
        return consent_token["TOKENN"]

    def startTokenServer(self):
        self.server = FlaskServer()
        self.server_t = Thread(target=self.server.run, daemon=True)
        self.server_t.start()
        self.server_running = True

class FlaskServer():
    def __init__(self, host="127.0.0.1", port="5000"):
        self.app = Flask(__name__)
        self.log = logging.getLogger('werkzeug')
        self.log.setLevel(logging.CRITICAL)
        self.log.disabled = True
        self.app.logger.disabled = True
        self.host = host
        self.port = port
        self.exiting = True
        self.consent_token = None

        @self.app.route('/send/accesstoken', methods=['POST'])
        def endpoint():
            input_json = request.get_json(force=True)
            dictToReturn = {'answer': 42}
            self.consent_token = input_json
            return jsonify(dictToReturn)

        @self.app.route('/retrieve/accesstoken', methods=['GET'])
        def requestpoint():
            start_time = timeit.default_timer()
            while not self.consent_token:
                elapsed = timeit.default_timer() - start_time
                if elapsed > 10:
                    dictToReturn = {'TIMEOUT': 0}
                    return jsonify(dictToReturn)
                continue
            requested_tok = self.consent_token.copy()
            self.consent_token = None
            return jsonify(requested_tok)

    def run(self):
        self.app.run(self.host, self.port)

class LinkScrape(HTMLParser):
    #Inspired by https://stackoverflow.com/a/36980627/13642249
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr in attrs:
                if attr[0] == 'href':
                    link = attr[1]
                    if link.find('http') >= 0:
                        self.links.append(link)

class Ngrok():
    def __init__(self):
        self.up = False
        self._ngrok_name = "ngrok.exe" if platform.system() == "Windows" else "ngrok"
        self.ngrok_path = Path(__file__).resolve(
        ).parent / "ngrok" / self._ngrok_name

        if not self.ngrok_path.is_file():
            self.download()

    def startProcess(self):
        if not self.up:
            cmd = f"{self.ngrok_path} http 5000 --log stdout".split()
            self.ngrok_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.up = True

    def download(self):
        ngrok_dir = Path(__file__).resolve().parent / "ngrok"
        ngrok_dir.mkdir(exist_ok=True)
        url = "https://ngrok.com/download"
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        response = requests.get(url, headers=headers)
        link_parser = LinkScrape()
        link_parser.feed(response.text)
        links = link_parser.links
        stable_downloads = [x for x in links if "stable" in x]
        windows_downloads = [x for x in stable_downloads if "windows" in x][0]
        linux_downloads = [x for x in stable_downloads if "linux" in x][0]
        osname = platform.system()
        if osname == 'Darwin':
            ver = "darwin-amd64"
            ver_to_download = re.sub("(?<=stable-)(.*)(?=.zip)", ver, windows_downloads, flags=re.DOTALL)            
        elif osname == 'Windows':
            if sysconfig.get_platform() == "win-amd64":
                ver = "windows-amd64"
                ver_to_download = re.sub("(?<=stable-)(.*)(?=.zip)", ver, windows_downloads, flags=re.DOTALL)
            else: #win32
                ver = "windows-386"
                ver_to_download = re.sub("(?<=stable-)(.*)(?=.zip)", ver, windows_downloads, flags=re.DOTALL)
            
        elif osname == 'Linux':
            if sysconfig.get_platform() == "linux-x86_64":
                ver = "linux-amd64"
                ver_to_download = re.sub("(?<=stable-)(.*)(?=.tgz)", ver, linux_downloads, flags=re.DOTALL)
            elif sysconfig.get_platform() == "linux-i686":
                ver = "linux-386"
                ver_to_download = re.sub("(?<=stable-)(.*)(?=.tgz)", ver, linux_downloads, flags=re.DOTALL)
            elif sysconfig.get_platform() == "linux-aarch64": #pi3B
                ver = "linux-arm"
                ver_to_download = re.sub("(?<=stable-)(.*)(?=.tgz)", ver, linux_downloads, flags=re.DOTALL)
        else:
            raise NotImplemented(f"Unknown OS '{osname}'")
        dl_zip = ngrok_dir / Path(ver_to_download).name
        with requests.get(ver_to_download,stream=True) as r:
            with open(dl_zip, "wb") as f:
                shutil.copyfileobj(r.raw, f)
        if Path(dl_zip).suffix == ".zip":
            with zipfile.ZipFile(dl_zip, "r") as zip_file:
                zip_file.extractall(ngrok_dir)
        else:
            with tarfile.open(dl_zip, "r") as tar:
                tar.extractall(ngrok_dir)
        os.remove(dl_zip)
        os.chmod(ngrok_dir/self._ngrok_name, 0o755) 
        
    def getUrl(self):
        while True:
            line = self.ngrok_process.stdout.readline()
            if not line and self.ngrok_process.poll() is not None:
                continue
            elif b'url=' in line:
                output = line.decode()
                tunnel_url = output.split()[-1].split("=")[1]
                break
        return tunnel_url

    def stopProcess(self):
        if self.up:
            self.ngrok_process.kill()
            self.ngrok_process = None
            self.up = False

if __name__ == "__main__":
    obj = Ngrok()
    print()
    # obj.download()

