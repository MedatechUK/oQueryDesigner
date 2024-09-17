import sys , json

from PyQt6.QtCore import Qt , QVariant
from PyQt6 import QtCore , QtGui, QtWidgets 
from PyQt6.QtWidgets import QTreeWidgetItem

# Local imports
import oQuery , widgets 

#region "EFORM URL"

def eform(Name=None):
    ret = "EFORM?$filter="
    if Name == None:
        ret += "RESTFLAG%20eq%20%27Y%27"
    else:
        ret += "ENAME%20eq%20%27" + Name + "%27"
    
    ret += "&$expand=FCLMN_SUBFORM($select=NAME,CNAME,READONLY,BOOLEAN,TYPE,WIDTH,COLTITLE,TITLE; $filter=(HIDEBOOL ne 'Y'); $orderby=ORD; $expand=FCLMNA_SUBFORM($select=TYPE)),FLINK_SUBFORM($select=FNAME,TITLE)"

    return ret

#endregion

#region "Tree Widget handlers"

def on_item_expanded(item):    
    for i in range(item.childCount()):
        c = item.child(i)           
        if c.FCLMN == None:            
            a.getURL( eform(c.Name)  , c.expandItem )  

def on_form_click(item):
    tabWidget.setCurrentIndex(0)
    ColumnWidget.on_form_click(item)

#endregion

#region "Column Widget handlers"

def on_ColumnSelect( Row ):
    if len(tree_widget.selectedItems()) > 0:
        ConditionWidget.on_form_click(tree_widget.selectedItems()[0] , Row )

#endregion

#region "Tabbed Widget handlers"

def onChangeLang():
    if ColumnWidget.Item != None and ColumnWidget.Item.Root().Check :                                            
        match lang.currentText():
            case "JavaScript":                
                    codeText.setPlainText(ColumnWidget.Item.Root().js_code()) 

            case "Python":
                codeText.setPlainText("import requests\nresponse = requests.get('" + a.URL() + ColumnWidget.Item.Root().safeURL() + "')\nprint(response.json())")
            case "C#":
                codeText.setPlainText("using System.Net.Http;\nusing System.Threading.Tasks;\n\nvar client = new HttpClient();\nvar response = await client.GetAsync('" + a.URL() + ColumnWidget.Item.Root().safeURL() + "');\nvar content = await response.Content.ReadAsStringAsync();\nConsole.WriteLine(content);")
            case "VB":
                codeText.setPlainText("Imports System.Net.Http\n\nDim client As New HttpClient()\nDim response = Await client.GetAsync('" + a.URL() + ColumnWidget.Item.Root().safeURL() + "')\nDim content = Await response.Content.ReadAsStringAsync()\nConsole.WriteLine(content)")                       

            case "node.js Router":
                ret = ""
                ret += "/* oData("+ ColumnWidget.Item.Root().Name +") Router. */\n"
                ret += "/* Save as ./public/routes/"+ ColumnWidget.Item.Root().Name +".js */\n"
                ret += "var express = require('express');\n"
                ret += "var cors = require('cors');\n"
                ret += "var router = express.Router();\n"
                ret += "var request = require('request') ;\n"                
                ret += "const { isNullOrUndefined } = require('util');\n"                
                ret += "\n"
                ret += "router.get('/', cors() ,function(req, res, next) {\n"                
                ret += "    var options = {\n"
                ret += "        method: 'get',\n"
                ret += "        url: '" + a.URL() + ColumnWidget.Item.Root().safeURL() + "',\n"
                ret += "        headers: { \n"
                ret += "            'Authorization': '"+ a.generate_basic_auth() +"'\n"
                ret += "        }\n"
                ret += "      };\n"                
                ret += "    request(options, function (error, response) {\n"
                ret += "        if (error) throw new Error(error);\n"
                ret += "        js = JSON.parse(response.body);\n"
                ret += "        res.json(js);\n"                
                ret += "    });   \n"                
                ret += "});\n"
                ret += "\n"                
                ret += "module.exports = router;\n"                
                codeText.setPlainText(ret)

    else:
        codeText.setPlainText("Please select a form and column")
        
def on_tab_changed(i):
    match i :        
        case 1:
            if ColumnWidget.Item != None and ColumnWidget.Item.Root().Check :                            
                url = ColumnWidget.Item.Root().URL()
                textedit.setText(a.URL() + url)
                textedit.setFocus()
            
            else:
                textedit.setPlaceholderText("Please select a form and column")
        
        case 2:
            if ColumnWidget.Item != None and ColumnWidget.Item.Root().Check :     
                onChangeLang()
                codeText.setFocus()
            
            else:
                codeText.setPlaceholderText("Please select a form and column")

        case _:
            textedit.setText("")
            textedit.setPlaceholderText("Please select a form and column")
            jsonViewer.clear()

#endregion

#region "Text Edit handlers"

def on_Refresh(url): 
    jsonViewer.clear()     
    a.getURL(url.split(a.URL())[1] , jsonViewer.load_json)    

#endregion

#region "Window handlers"

def closeEvent(event):
    #tree_widget.save_state()
    super().closeEvent(event)

#endregion

if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = widgets.CustomMainWindow() #QtWidgets.QMainWindow()
    MainWindow.Close.connect(lambda e: closeEvent(e))

    ui = oQuery.Ui_MainWindow()
    ui.setupUi(MainWindow)        

    # Assuming 'ui' is your main window or widget containing the treeWidget
    tree_widget = ui.treeWidget
    # Connect the signals to the custom slot
    tree_widget.item_Expanded.connect(on_item_expanded)
    tree_widget.item_click.connect(on_form_click)    
    # tree_widget.load_state()
    
    ColumnWidget = ui.columnWidget
    # Connect the signals to the custom slot
    ColumnWidget.Select.connect(on_ColumnSelect)

    ConditionWidget = ui.conditionWidget

    textedit = ui.textEdit
    # Connect the signals to the custom slot
    textedit.refresh.connect(on_Refresh)
    
    tabWidget = ui.tabWidget
    tabWidget.setCurrentIndex(0)
    tabWidget.currentChanged.connect(lambda i: on_tab_changed(i))

    jsonViewer = ui.widget
    lang = ui.lang    
    lang.addItem("Python")    
    lang.addItem("C#")
    lang.addItem("VB")    
    lang.addItem("node.js Router")
    lang.addItem("JavaScript")
    
    lang.currentIndexChanged.connect(onChangeLang)

    codeText = ui.codeText

    a = widgets.AsyncoDataRequest(
        baseurl    = "prioritydev.clarksonevans.co.uk"
        , env      = "fuld1"
        , user     = ""
        , password = ""  
    )    
    
    while not ( a.Cancel | a.LoginOK ) :
        a.getURL(eform(), tree_widget.on_load)    

    if a.Cancel:
        sys.exit()
    
    else:        
        MainWindow.setWindowTitle((f"oQuery Designer | {a.baseurl.split("://")[1]}") )
        MainWindow.show()    
        sys.exit(app.exec())
