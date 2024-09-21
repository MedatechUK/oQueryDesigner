import json , pickle
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtWidgets import QTreeWidgetItem , QTableWidget
from PyQt6.QtGui import QTextOption , QFocusEvent
from PyQt6.QtWidgets import QDialog

#region "CustomMainWindow"

class CustomMainWindow(QtWidgets.QMainWindow):

    Close = pyqtSignal(QtCore.QEvent)    
    loginEvent = pyqtSignal(str,str,str,str)   

    def __init__(self , parent=None) :
        super().__init__()
        
    def closeEvent(self, event):          
        super().closeEvent(event)        

#endregion
        
#region "Tree Widgets"

class CustomTreeWidget(QtWidgets.QTreeWidget):

    # Define a custom role
    ENAME = Qt.ItemDataRole.UserRole + 1
    FCLMN = Qt.ItemDataRole.UserRole + 2

    @property
    def fc(self):
        return self.currentItem().data(0, self.FCLMN).get("FCLMN")

    @fc.setter
    def fc(self, value):
        self.currentItem().setData(0, self.FCLMN, {"FCLMN": value})

    @property
    def en(self):
        return self.currentItem().data(0, self.ENAME).get("ENAME")

    item_click = pyqtSignal(QTreeWidgetItem)
    item_Expanded = pyqtSignal(QTreeWidgetItem)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.itemClicked.connect(self.on_item_clicked)
        self.itemExpanded.connect(self.on_item_expanded)
        self.itemChanged.connect(self.on_item_check_state_changed)

    def on_load(self , data):
        # Get the data from the API
        for i in [i for i in data['value'] if i['ENAME'] != "EFORM"] :
            
            # Create a new item
            item = CustomQTreeWidgetItem(name=i['ENAME'] , title=i['TITLE'])
            item.FCLMN = i["FCLMN_SUBFORM"]                       
            
            # Add the item to the tree widget
            self.addTopLevelItem(item)

            for c in i['FLINK_SUBFORM']:
                child_item = CustomQTreeWidgetItem(name=c['FNAME'] , title=c['TITLE'])            
                item.addChild(child_item)
                
    def __getstate__(self):
        # Serialize the tree widget items
        state = []
        for i in [i for i in range(self.topLevelItemCount()) if self.topLevelItem(i).checkState(0) == Qt.CheckState.Checked]:
            item = self.topLevelItem(i)
            state.append(self._serialize_item(item))
        return state

    def __setstate__(self, state):
        super().__init__()
        # Clear the current items
        self.clear()
        # Deserialize the state and add items back to the tree widget
        for item_data in state:
            item = self._deserialize_item(item_data)
            self.addTopLevelItem(item)

    def _serialize_item(self, item):
        # Recursively serialize a QTreeWidgetItem
        item_data = {
            "Title": item.Title,
            "Check": item.Check,
            "FCLMN": item.FCLMN,
            "Name": item.Name,
            "children": [self._serialize_item(item.child(i)) for i in [i for i in range(item.childCount()) if item.child(i).Check]]
        }
        return item_data

    def _deserialize_item(self, item_data):
        # Recursively deserialize a QTreeWidgetItem
        # Create a new item
        item = CustomQTreeWidgetItem(name=item_data["Name"] , title=item_data["Title"])
        item.FCLMN = item_data["FCLMN"]
        item.Check = item_data["Check"]

        for child_data in item_data["children"]:
            child_item = self._deserialize_item(child_data)
            item.addChild(child_item)

        return item
    
    def on_item_check_state_changed(self, item, column):
        if column == 0:  # Assuming the checkbox is in the first column
            match item.checkState(0):
                case Qt.CheckState.Checked:
                    item.Check = True
                    self.check_all_parents(item)                    
                case Qt.CheckState.Unchecked:
                    item.Check = False
                    self.uncheck_all_children(item)

    def on_item_clicked(self, item, column):
        self.item_click.emit(item)

    def on_item_expanded(self, item):
        self.item_Expanded.emit(item)

    def check_all_parents(self, item):
        parent = item.parent()
        while parent:
            parent.setCheckState(0, Qt.CheckState.Checked)
            parent = parent.parent()

    def uncheck_all_children(self, item):
        def recursive_uncheck(item):
            for i in range(item.childCount()):
                child = item.child(i)
                child.setCheckState(0, Qt.CheckState.Unchecked)
                recursive_uncheck(child)
        recursive_uncheck(item)

    def save_treewidget_state(self , treewidget, filename):
        with open(filename, 'wb') as file:
            pickle.dump(treewidget, file)

    def load_treewidget_state(self , filename):    
        with open(filename, 'rb') as file:
            return pickle.load(file)

    def save_state(self):
        self.save_treewidget_state(self, 'treewidget_state.pkl')

    def load_state(self):
        try:
            loaded_treewidget = self.load_treewidget_state('treewidget_state.pkl')            
            i = loaded_treewidget.takeTopLevelItem(0)
            while i:
                for t in range(self.topLevelItemCount()):
                    if self.topLevelItem(t).Name == i.Name:                        
                        self.topLevelItem(t).load(self.topLevelItem(t), i)
                        break                
                i = loaded_treewidget.takeTopLevelItem(0)

        except (FileNotFoundError, pickle.UnpicklingError):
            pass

class CustomQTreeWidgetItem(QTreeWidgetItem):        

    def __init__(self, name=None, title=None, parent=None):
        super().__init__(parent)
        self.FCLMN = None
        if name is not None:
            self.Name = name
        if title is not None:
            self.Title = title

        self.Name = name
        self.setText(0, title)  # Set text for the first column        
        self.setFlags(self.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        self.setCheckState(0, Qt.CheckState.Unchecked)

    def load(self, olditem , item ):      
        olditem.setExpanded(True)
        self.FCLMN = item.FCLMN
        self.Check = item.Check        
        for i in range(olditem.childCount()):
            for j in range(item.childCount()):
                if self.child(i).Name == item.child(j).Name:
                    self.child(i).load(olditem.child(i), item.child(j))


        
    def expandItem(self, data):
        self.FCLMN = data['value'][0]["FCLMN_SUBFORM"]            

        for i in data['value']:
            if 'FLINK_SUBFORM' in i:
                for s in i['FLINK_SUBFORM']:
                    child_item = CustomQTreeWidgetItem(name=s['FNAME'] , title=s['TITLE'])                                                
                    self.addChild(child_item)        

    # Returns the root item of the selected item
    def Root(self) :
        parent = self
        while parent.parent():
            parent = parent.parent()
        return parent
    
    # RETURNS TRUE IF NO CHILDREN ARE SELECTED
    def selectAll(self) -> bool:
        for i in self.FCLMN:
            if i["CHECKED"] == "Y":
                return False
                break
        return True
    
#region "CustomQTreeWidgetItem Properties"

    NAME_ROLE = Qt.ItemDataRole.UserRole + 1
    TITLE_ROLE = Qt.ItemDataRole.UserRole + 2
    FCLMN_ROLE = Qt.ItemDataRole.UserRole + 3
    CHECK_ROLE = Qt.ItemDataRole.UserRole + 4

    @property
    def Name(self):
        return self.data(0, self.NAME_ROLE)

    @Name.setter
    def Name(self, value):
        self.setData(0, self.NAME_ROLE, value)

    @property
    def Title(self):
        return self.data(0, self.TITLE_ROLE)

    @Title.setter
    def Title(self, value):
        self.setData(0, self.TITLE_ROLE, value)

    @property
    def FCLMN(self):
        return self.data(0, self.FCLMN_ROLE)

    @FCLMN.setter
    def FCLMN(self, value):        
        if value!=None:
            for c in value:
                if "CHECKED" not in c:
                    c["CHECKED"] = ""        
                if "oSORT" not in c:
                    c["oSORT"] = ""
        self.setData(0, self.FCLMN_ROLE, value)

    @property
    def Check(self):
        return self.data(0, self.CHECK_ROLE)

    @Check.setter
    def Check(self, value):
        self.setData(0, self.CHECK_ROLE, value)
        match value:
            case True:
                self.setCheckState(0, Qt.CheckState.Checked)
            case False:
                self.setCheckState(0, Qt.CheckState.Unchecked)
#endregion

#region "oData URL Generation"

    def select(self):
        ret = []    
        for i in self.FCLMN:
            if i["CHECKED"] == "Y":                
                ret.append( i["NAME"] )
        
        if len(ret) == 0:
            return ""
        else:            
            return "$select=" + ",".join(ret)

    def sort(self):
        ret = []    
        for i in [i for i in self.FCLMN if i["oSORT"] != ""] :
            match i["oSORT"]:
                case "ASC":
                    ret.append(i["NAME"])
                case "DESC":
                    ret.append(i["NAME"] + " desc")                
        
        if len(ret) == 0:
            return ""
        else:            
            return "$orderby=" + ",".join(ret)
            
    def filter(self):
        ret2 = []
        for i in self.FCLMN:
            if "CONDITIONS" in i:                            
                ret = []
                count = 0
                for c in i["CONDITIONS"]:
                    if count > 0:
                        ao = c["andor"] + " " + i["NAME"]
                    else:
                        ao = i["NAME"]
                    
                    colType = i["TYPE"]
                    if colType == None:
                        colType = i["FCLMNA_SUBFORM"]["TYPE"]

                    match colType:
                        case "INT" :
                            val = str(c["value"])
                        case "REAL":
                            val = str(c["value"])
                        case _:
                            val = "'" + str(c["value"]) + "'"

                    match c["compare"]:
                        case "=":
                            ret.append(ao + " eq " + val)
                        case "<>":
                            ret.append(ao + " ne " + val)
                        case ">", ">=":
                            ret.append(ao + " gt " + val if c["compare"] == ">" else ao + " ge " + val)
                        case "<", "<=":
                            ret.append(ao + " lt " + val if c["compare"] == "<" else ao + " le " + val)

                    count += 1

                if len(ret) > 0:
                    ret2.append("(" + " ".join(ret) + ")")

        if len(ret2) == 0:
            return ""
        else:
            return "$filter=" + " and ".join(ret2)
    
    def expand(self):
        ch = []
        for i in [i for i in range(self.childCount()) if self.child(i).Check]:            
            curl = self.child(i).URL()
            if len(curl) > 0: curl = "(" + curl + ")"                                        
            ch.append(self.child(i).Name + "_SUBFORM" + curl)
        
        if len(ch) > 0:            
            return "$expand=" + ",".join(ch) 
        else:
            return ""

    def URL(self):
        ret= ""
        if self.parent() == None:
            ret = self.Name + "?\n"         
            delim = "&"
        else:            
            delim = "; "

        fpar = []
        sel = self.select()
        if len(sel) > 0 : fpar.append(sel)
        filt = self.filter()
        if len(filt) > 0 : fpar.append(filt)
        ord = self.sort()
        if len(ord) > 0 : fpar.append(ord)
        exp = self.expand()
        if len(exp) > 0 : fpar.append(exp)
        
        if len(fpar) > 0:
            if self.parent() != None: ret += "\n"

        return ret + delim.join(fpar)         

    def safeURL(self):
        return self.URL().replace(chr(10),"").replace(chr(13),"").replace(chr(8),"")
    
#endregion

#region "Javascript Code Generation"

    def tabstr(self,tabs):
        return ' ' * 4 * tabs
    
    def js_code(self,tabs=0):
        ret = ""
        if self.parent() == None:
            ret += "// oData "+ self.Name +" Marker Object. \n\n"

            ret +="// The "+ self.Name +" info window class, which extends the infoWindow class.\n"
            ret +="class nfo"+ self.Name +" extends infoWindow {\n"
            ret +="    constructor() {\n"
            ret +="        super();\n"
            ret +="    }\n"
            ret +="    refresh(data){\n"
            ret +="        // Refresh the contents of the window with (data)\n"
            ret +="        x = '<h1>Placeholder</h1>'\n"
            ret +="        infowindowContent.innerHTML = x;\n"
            ret +="        return infowindowContent;\n"
            ret +="    }\n"
            ret +="}\n\n"

            ret += "// The "+ self.Name +" marker class, which extends the markerClass.\n"
            ret += "class "+ self.Name +"Marker extends markerClass {\n"
            ret += "    constructor(parent, lat, long , nfo) {\n"
            ret += "        super(parent , lat, long, nfo);\n"
            ret += '        this.label = "Some Label"\n'
            ret += "        this.color = '#c0c0c0'\n"
            ret += "    }\n"
            ret += "    getIcon(){\n"
            ret += "        return {\n"
            ret += "            path: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z',\n"
            ret += "            fillColor: this.color,\n"
            ret += "            fillOpacity: 0.6,\n"
            ret += "            scale: 1,\n"
            ret += "            strokeColor: '#000000',\n"
            ret += "            strokeWeight: 2\n"
            ret += "        };\n"
            ret += "    }\n"
            ret += "}\n\n"    

            ret += "// The "+ self.Name +" class, which extends the oDataClass class.\n"     
            ret += self.tabstr(tabs) + "class "+ self.Name +" extends oDataClass {\n"
            tabs +=1
            ret += self.tabstr(tabs) + "// The constructor\n"
            ret += self.tabstr(tabs) + "constructor() {\n"
            ret += self.tabstr(tabs) + "    // Call the parent constructor\n"
            ret += self.tabstr(tabs) + '    super("' + self.Name + '");\n'            
            ret += self.tabstr(tabs) + "}\n"
     
            ret += self.tabstr(tabs) + "// #region Methods to be implemented by derived class\n"
            ret += self.tabstr(tabs) + "URL(){\n"
            ret += self.tabstr(tabs) + "    // Get the URL for the oData service\n"
            ret += self.tabstr(tabs) + '    return "' + self.safeURL() + '";\n'
            ret += self.tabstr(tabs) + "}\n"            
            ret += self.tabstr(tabs) + "// Set the markers in item\n"    
            ret += self.tabstr(tabs) + "setMarkers(item){\n"
            ret += self.tabstr(tabs) + '    // Create marker named "DEFAULT"\n'
            ret += self.tabstr(tabs) + '    item.markers.push["DEFAULT"];\n'
            ret += self.tabstr(tabs) + '    // Create the nfo' + self.Name +'" info window\n'
            ret += self.tabstr(tabs) + '    var info = new nfo' + self.Name +'();\n'
            ret += self.tabstr(tabs) + '    // Set the "DEFAULT" markers data, location and window\n'
            ret += self.tabstr(tabs) + '    item.markers["DEFAULT"] =\n'
            ret += self.tabstr(tabs) + '        new ' + self.Name +'Marker(item, item.LAT, item.LONG , info);\n'
            ret += self.tabstr(tabs) + "}\n"
            
            ret += self.tabstr(tabs) + "Visible(item , marker){\n"
            ret += self.tabstr(tabs) + "    // Set the marker visibility (and other properties) \n"
            ret += self.tabstr(tabs) + "    return false;\n"
            ret += self.tabstr(tabs) + "}\n"            
            ret += self.tabstr(tabs) + "onLoad(response){\n"
            tabs +=1
            ret += self.tabstr(tabs) + "// Handle the response from the oData service\n"
            
        else:
            ret += self.tabstr(tabs) + self.Name + "_SUBFORM : i." + self.Name + "_SUBFORM.map(function (i, index) {\n"
        
        
        ret += self.tabstr(tabs) + "let o" + self.Name + " = {\n"        
        tabs += 1

        ret += self.tabstr(tabs) + "ID: index,\n"
        
        if self.selectAll():
            for i in self.FCLMN:
                ret += self.tabstr(tabs) + i["NAME"] + ": i." + i["NAME"] + ",\n"
        else:
            for i in [i for i in self.FCLMN if i["CHECKED"] == "Y"]:
                ret += self.tabstr(tabs) + i["NAME"] + ": i['" + i["NAME"] + "'],\n"

        for i in [i for i in range(self.childCount()) if self.child(i).Check]:            
            ret += self.child(i).js_code(tabs)  
             
        tabs -= 1

        ret += self.tabstr(tabs) + "}\n" 
        ret += self.tabstr(tabs) + "return o" + self.Name + ";\n"        

        if self.parent() == None:                                                   
            tabs -= 1
            ret += self.tabstr(tabs) + "}\n"
            ret += self.tabstr(tabs) + "// #endregion\n"
            tabs -= 1
            ret += self.tabstr(tabs) + "}\n"                        
            

        else:            
            ret += self.tabstr(tabs) + "}),\n"             

        return ret
    
#endregion

#endregion

#region "Table Widgets"

class ColumnWidget(QTableWidget):
    
    Select = pyqtSignal(int)    

    def __init__(self, name=None, title=None, parent=None):
        super().__init__(parent)
        
        self.Item = None
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels(["Select", "Name", "Title", "Type" , "Sort","!="])        
        self.setColumnWidth(0, 25)
        self.setColumnWidth(1, 150)
        self.setColumnWidth(2, 150)
        self.setColumnWidth(3, 60)
        self.setColumnWidth(4, 100)
        self.setColumnWidth(5, 25)
        self.itemSelectionChanged.connect(self.on_item_selection_changed)

    def on_item_selection_changed(self ):
         self.Select.emit(self.currentRow()-1)

    def sel(self):
        if self.Item.checkState(0) != Qt.CheckState.Checked:
            tmp = self.Item.FCLMN
            for i in tmp:
                i["CHECKED"] = "N"
            self.Item.FCLMN = tmp
            return False
        else:
            for i in self.Item.FCLMN:       
                if i["CHECKED"] == "Y":
                    return False
        return True

    def on_form_click(self , item):

        self.Item = item
        self.setRowCount(0)

        row_position = self.rowCount()
        self.insertRow(row_position)
        
        self.selectAll = tbl_checkBox(row_position=row_position, Name="Select" , SelValue=self.sel())
        self.selectAll.changed.connect(self.on_select_all)

        self.setCellWidget(row_position, 0, self.selectAll)        
        self.setCellWidget(row_position, 1 , tbl_label(row_position=row_position, Name="Name" , SelValue="Select All"))
        self.setCellWidget(row_position, 2 , tbl_label(row_position=row_position, Name="Title" , SelValue="Select All"))
        self.setCellWidget(row_position, 3 , tbl_label(row_position=row_position, Name="Type" , SelValue="-"))
        self.setCellWidget(row_position, 4 , tbl_label(row_position=row_position, Name="Sort" , SelValue="-"))
        self.setCellWidget(row_position, 5 , tbl_label(row_position=row_position, Name="Sort" , SelValue="-"))

    
        for i in item.FCLMN:        

            # Add a new row to the ConditionWidget
            row_position = self.rowCount()
            self.insertRow(row_position)
            
            W0 = tbl_checkBox(row_position=row_position-1, Name="Select" , SelValue=i["CHECKED"]=="Y")
            W0.changed.connect(self.on_change)
            self.setCellWidget(row_position, 0, W0)
            
            W1 = tbl_label(row_position=row_position-1, Name="Name" , SelValue=i["NAME"])            
            self.setCellWidget(row_position, 1, W1)
            
            if i["TITLE"] != None:
                TITLE = i["TITLE"]
            else:
                if i["COLTITLE"] != None:
                    TITLE = i["COLTITLE"]
                else:
                    TITLE = i["NAME"]
            
            W2 = tbl_label(row_position=row_position-1, Name="Title" , SelValue=TITLE)            
            self.setCellWidget(row_position, 2, W2)
            
            match i["TYPE"]:
                case None:
                    W3 = tbl_label(row_position=row_position-1, Name="Type" , SelValue=i["FCLMNA_SUBFORM"]["TYPE"])            
                case _:
                    W3 = tbl_label(row_position=row_position-1, Name="Type" , SelValue=i["TYPE"])                        
            self.setCellWidget(row_position, 3, W3)

            W5 = tbl_comboBox(row_position=row_position-1, Name="Sort" , SelValue=i["oSORT"] , Items=["","ASC", "DESC"])
            W5.changed.connect(self.on_change)
            self.setCellWidget(row_position, 4, W5)   

            W6 = tbl_pushButton(row_position=row_position, Name="AddCondition" , SelValue="!=")
            W6.changed.connect(self.on_change)                                 
            self.setCellWidget(row_position, 5, W6)                

    def on_change(self , Name, Row , Widget):
        tmp = self.Item.FCLMN
        match Name:
            case "AddCondition":
                # Implement the logic for adding a condition to the item
                tmp = self.Item.FCLMN            
                if not "CONDITIONS" in tmp[Row-1]:  
                    tmp[Row-1]["CONDITIONS"] = []        
                if len(tmp[Row-1]["CONDITIONS"]) > 0:
                    tmp[Row-1]["CONDITIONS"].append({"andor": "AND", "compare": "=", "value": ""})
                else:
                    tmp[Row-1]["CONDITIONS"].append({"andor": "", "compare": "=", "value": ""})

                self.Item.FCLMN = tmp      
                self.Select.emit(Row-1)

            case "Select":                                                
                tmp[Row]["CHECKED"] = "Y" if Widget.isChecked() else "N"                                    
                if tmp[Row]["CHECKED"] == "Y" :
                    self.selectAll.setChecked(False)
                    self.Item.Check = True

            case "Sort":    
                tmp[Row]["oSORT"] = Widget.currentText()
            
            case _: 
                pass
        
        self.Item.FCLMN = tmp

    def on_select_all(self):
        if self.selectAll.isChecked():
            self.Item.Check = True
            tmp = self.Item.FCLMN
            for i in tmp:
                i["CHECKED"] = "N"
            self.Item.FCLMN = tmp
            self.on_form_click(self.Item)

class ConditionWidget(QTableWidget):
    
    def __init__(self, name=None, title=None, parent=None):
        super().__init__(parent)
        
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(["And/Or", "Compare", "Value","Delete"])        

    def on_form_click(self , item , Row ):

        self.Item = item
        self.Row = Row        

        self.setRowCount(0)
        if self.Row >= 0:
            i = item.FCLMN[Row]
            if "CONDITIONS" in i:
                for c in i["CONDITIONS"]:
                    # Add a new row to the ConditionWidget
                    row_position = self.rowCount()
                    self.insertRow(row_position)

                    if row_position == 0 :
                        W0 = tbl_label(row_position=row_position, Name="AndOr" , SelValue="")
                    else:
                        W0 = tbl_comboBox(row_position=row_position, Name="AndOr" , SelValue=c["andor"], Items=["","AND", "OR"])       
                        W0.changed.connect(self.on_change)                                 
                    self.setCellWidget(row_position, 0, W0)

                    W1 = tbl_comboBox(row_position=row_position, Name="Compare", SelValue=c["compare"],Items=["","=", "<>", ">", "<", ">=", "<="])
                    W1.changed.connect(self.on_change)                                 
                    self.setCellWidget(row_position, 1, W1) 
                    
                    W2 = tbl_textbox(row_position=row_position, Name="Value" , SelValue=c["value"])
                    W2.changed.connect(self.on_change)                                 
                    self.setCellWidget(row_position, 2, W2)

                    W3 = tbl_pushButton(row_position=row_position, Name="Delete" , SelValue="Delete")
                    W3.changed.connect(self.on_change)                                 
                    self.setCellWidget(row_position, 3, W3)

    def on_change(self , Name, Row , Widget):
        tmp = self.Item.FCLMN
        match Name:
            case "AndOr":                                                                
                tmp[self.Row]["CONDITIONS"][Row]["andor"] = Widget.currentText()

            case "Compare":    
                tmp[self.Row]["CONDITIONS"][Row]["compare"] = Widget.currentText()
            
            case "Value":
                tmp[self.Row]["CONDITIONS"][Row]["value"] = Widget.text()

            case "Delete":
                tmp[self.Row]["CONDITIONS"].pop(Row)                

            case _: 
                pass
        
        self.Item.FCLMN = tmp
        match Name:
            case "Delete":
                self.on_form_click(self.Item , self.Row)         
        
#endregion

#region "Table Widgets Controls"

class tbl_textbox(QtWidgets.QLineEdit):
    changed = pyqtSignal(str, int , QtWidgets.QLineEdit)

    def __init__(self, Name=None, parent=None, row_position=0, SelValue=""):
        super().__init__(parent)
        self.Name = Name
        self.setText(SelValue)
        self.editingFinished.connect(lambda: self.on_editing_finished(row_position))

    def on_editing_finished(self, row_position):
        self.changed.emit(self.Name, row_position, self)
    
class tbl_label(QtWidgets.QLabel):
    changed = pyqtSignal(str, int , QtWidgets.QLabel)

    def __init__(self, Name=None, parent=None, row_position=0, SelValue=""):
        super().__init__(parent)
        self.Name = Name
        self.setText(SelValue)
            
class tbl_comboBox(QtWidgets.QComboBox):
    changed = pyqtSignal(str , int , QtWidgets.QLineEdit)
    def __init__(self, Name=None, parent=None, row_position=0, SelValue="", Items=[]):
        super().__init__(parent)
        self.Name = Name        
        self.addItems(Items)
        self.setCurrentText(SelValue)    
        self.currentIndexChanged.connect(lambda: self.on_currentIndexChanged(row_position))

    def on_currentIndexChanged(self, row_position):
        self.changed.emit(self.Name, row_position, self)    

class tbl_checkBox(QtWidgets.QCheckBox):
    changed = pyqtSignal(str, int , QtWidgets.QCheckBox)
    def __init__(self, Name=None, parent=None, row_position=0, SelValue=False):
        super().__init__(parent)
        self.Name = Name        
        self.setChecked(SelValue)
        self.stateChanged.connect(lambda: self.on_stateChanged(row_position))

    def on_stateChanged(self, row_position):
        self.changed.emit(self.Name, row_position, self)

class tbl_pushButton(QtWidgets.QPushButton):
    changed = pyqtSignal(str, int , QtWidgets.QPushButton)
    def __init__(self, Name=None, parent=None, row_position=0, SelValue=""):
        super().__init__(parent)
        self.Name = Name        
        self.setText(SelValue)
        self.clicked.connect(lambda: self.on_clicked(row_position))

    def on_clicked(self, row_position):
        self.changed.emit(self.Name, row_position, self)
        
#endregion        

#region "Text Widgets"

class CustomTextedit(QtWidgets.QTextEdit):

    refresh = pyqtSignal(str)   

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(False)
        self.setTabChangesFocus(True)
        self.setLineWrapMode(QtWidgets.QTextEdit.LineWrapMode.NoWrap)
        self.setPlaceholderText("Enter the URL here")

        # Disable horizontal scrolling
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWordWrapMode(QTextOption.WrapMode.WordWrap)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == Qt.Key.Key_F5:            
            self.refresh.emit(self.URL())        

    def URL(self):
        return self.toPlainText().replace(chr(10),"").replace(chr(13),"").replace(chr(8),"")
        
class JsonViewer(QWidget):

    def __init__(self, parent=None):
        super().__init__()        
        layout = QVBoxLayout()
        self.textEdit = QTextEdit(self)
        self.textEdit.setReadOnly(True)
        layout.addWidget(self.textEdit)

        self.setLayout(layout)    

    def load_json(self, json_data):
        formatted_json = json.dumps(json_data, indent=4)
        self.textEdit.setPlainText(formatted_json)

    def clear(self):
        self.textEdit.clear()   

#endregion

#region "asynchronous URL request"

import aiohttp
import asyncio
import base64

class AsyncoDataRequest(QWidget):

    def __init__(self, baseurl=None, env=None, user=None, password=None):
        super().__init__()      
               
        self.baseurl = baseurl.rstrip('/')
        if "://" not in self.baseurl:
            self.baseurl = "https://" + self.baseurl
        self.env = env
        self.user = user
        self.password = password
        self.tabulaini = "tabula.ini"

        self.Cancel = False
        self.LoginOK = False
        self.LoginFail = False

    def MissingParams(self)->bool:
        return self.baseurl == None or self.env == None or self.user == None or self.password == None
         
    def URL(self):
        return self.baseurl + "/odata/priority/"+ self.tabulaini +"/" + self.env + "/"

    def generate_basic_auth(self):
        credentials = f"{self.user}:{self.password}"
        return f"Basic {base64.b64encode(credentials.encode('utf-8')).decode('utf-8')}"
                                               
    def getURL(self, url, callback):        
        
        if self.MissingParams():
            self.LoginFail = True

        if self.LoginFail:
            self.show_login_dialog()

        if not self.Cancel:
            # Run the asynchronous function in the event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If the event loop is already running, create a new one
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                new_loop.run_until_complete(self.asyncget(url, callback))
                asyncio.set_event_loop(loop)
            else:
                loop.run_until_complete(self.asyncget(url, callback ))           
        
    async def asyncget(self , url , callback):        
        async with aiohttp.ClientSession(auth=aiohttp.BasicAuth(self.user, self.password)) as session:
            async with session.get(self.URL() + url) as response:
                match response.status:
                    case 200:           
                        self.LoginOK = True
                        self.LoginFail = False
                        try:
                            callback(await response.json())

                        except Exception as e:
                            callback({"error": str(e)}) 

                    case _:                        
                        if not self.LoginOK: 
                            self.LoginFail = True
                        
                        else:
                            try:
                                callback(await response.json())

                            except Exception as e:                            
                                callback({"error": response.status , "message": response.reason})

#region "Show login dialog"
        
    def show_login_dialog(self):
        
            Dialog = QtWidgets.QDialog()
            dialogui = Ui_Dialog()
            dialogui.setupUi(Dialog)

            dialogui.url.setText(self.baseurl.split("://")[1])
            dialogui.env.setText(self.env)
            dialogui.username.setText(self.user)
            dialogui.password.setText(self.password)

            if Dialog.exec() == QDialog.DialogCode.Accepted:
                self.baseurl = dialogui.url.text().rstrip('/')
                if "://" not in self.baseurl:
                    self.baseurl = "https://" + self.baseurl
                self.env = dialogui.env.text()
                self.user = dialogui.username.text()
                self.password = dialogui.password.text()
            else:
                self.Cancel = True

#endregion                

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(390, 148)
        self.gridLayoutWidget = QtWidgets.QWidget(parent=Dialog)
        self.gridLayoutWidget.setGeometry(QtCore.QRect(10, 10, 371, 141))
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.gridLayout = QtWidgets.QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.gridLayout.addItem(spacerItem, 5, 1, 1, 1)
        self.label_2 = QtWidgets.QLabel(parent=self.gridLayoutWidget)
        self.label_2.setMinimumSize(QtCore.QSize(100, 0))
        self.label_2.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.label = QtWidgets.QLabel(parent=self.gridLayoutWidget)
        self.label.setMinimumSize(QtCore.QSize(100, 0))
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.label_3 = QtWidgets.QLabel(parent=self.gridLayoutWidget)
        self.label_3.setMinimumSize(QtCore.QSize(100, 0))
        self.label_3.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)
        self.label_4 = QtWidgets.QLabel(parent=self.gridLayoutWidget)
        self.label_4.setMinimumSize(QtCore.QSize(100, 0))
        self.label_4.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 3, 0, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(parent=self.gridLayoutWidget)
        self.buttonBox.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.StandardButton.Cancel|QtWidgets.QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 4, 1, 1, 1)
        self.url = QtWidgets.QLineEdit(parent=self.gridLayoutWidget)
        self.url.setObjectName("url")
        self.gridLayout.addWidget(self.url, 0, 1, 1, 1)
        self.env = QtWidgets.QLineEdit(parent=self.gridLayoutWidget)
        self.env.setObjectName("env")
        self.gridLayout.addWidget(self.env, 1, 1, 1, 1)
        self.username = QtWidgets.QLineEdit(parent=self.gridLayoutWidget)
        self.username.setObjectName("username")
        self.gridLayout.addWidget(self.username, 2, 1, 1, 1)
        self.password = QtWidgets.QLineEdit(parent=self.gridLayoutWidget)
        self.password.setInputMask("")
        self.password.setMaxLength(32767)
        self.password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.password.setObjectName("password")
        self.gridLayout.addWidget(self.password, 3, 1, 1, 1)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept) # type: ignore
        self.buttonBox.rejected.connect(Dialog.reject) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Log in"))
        self.label_2.setText(_translate("Dialog", "Priority Company:"))
        self.label.setText(_translate("Dialog", "oData Server:"))
        self.label_3.setText(_translate("Dialog", "Username:"))
        self.label_4.setText(_translate("Dialog", "Password"))
   
#endregion