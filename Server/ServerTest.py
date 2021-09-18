from flask import Flask, request
from urllib.parse import unquote
import sys 
sys.path.append("d:\\ProjectCode\\EngineeringAutomation\\InfoStatistics\\InfoStatisticsServer")
print(sys.path)
from ProcessService.ProcessService import ProcessService
app = Flask("newapp")


def GetGerberFiles(request_data):
    datas = request_data.split('_')
    gerbers = {}
    for data in datas:
        if len(data) == 0:
            continue
        datasp = data.split(':')
        gbname = datasp[0]
        gbdata = datasp[1]
        gerbers[gbname] = gbdata
    return gerbers


@app.route('/luolineslayer', methods=['POST', 'GET'])
def luolineslayer():
    if request.method == 'POST':
        data = request.form['gerberData']
        gerbers = GetGerberFiles(data)
        processService = ProcessService(gerbers)
        result = processService.routLineProcess.ToGerberFile()
        return result
    return "noGerberFile"


@app.route('/getgerberinfo', methods=['POST', 'GET'])
def getgerberinfo():
    if request.method == 'POST':
        data = request.form['gerberData']
        gerbers = GetGerberFiles(data)
        processService = ProcessService(gerbers)
        result = processService.GetInfoAnalysisResult()
        return result
    return "noGerberFile"


if __name__ == '__main__':
    app.run()
