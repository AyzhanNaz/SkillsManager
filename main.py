import sys
from owlready2 import *
from PyQt5 import uic, QtGui  # Импортируем uic
from PyQt5.QtCore import QItemSelectionModel
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeView, QTreeWidget, QTreeWidgetItem, QAbstractItemView, \
    QListWidgetItem, QListWidget, QVBoxLayout, QLabel, QAction, QWidget


class SkillWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Компетенции образовательной программы")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setGeometry(300, 300, 600, 600)


class MyWidget(QMainWindow):
    expandFlag = 0 # Состояние раскрытия списка курсов
    def __init__(self):
        super().__init__()
        uic.loadUi('skillmanager.ui', self)  # Загружаем дизайн
        self.initUI()
        self.loadOntolory("/Users/kda/Documents/Интеллектуальные информационные системы/Модель компетенций/competencies2.rdf")

    def initUI(self):
        self.treeView.clicked.connect(self.view_doubleClicked)
        self.expandAllButton.clicked.connect(self.view_expandAll)
        self.showComp.triggered.connect(self.showCompWindow)
        self.toggleReasonerCheckBox.stateChanged.connect(self.toggle_reasoner)

    def closeEvent(self, event):
        for window in QApplication.topLevelWidgets():
            window.close()


    # Рекурсивная фнукция получения дочерних компетенций
    def get_skills(self, skill, i, parent):
        skills = list(default_world.sparql("""
                prefix enu: <http://www.enu.kz/ontologies/curriculum#>
               SELECT ?s
               WHERE {
               ?s enu:isPartOf ?x.
               ?s rdfs:label ?l
                ?x rdfs:label '""" + skill[0].label[0] + """'
               }
                ORDER BY ?s
        """))
        print(skills)
        i += 1
        for skill in skills:
            child = QStandardItem(skill[0].name + ' ' + skill[0].label[0])
            parent.appendRow(self.get_skills(skill, i, child))
        return parent

    # Онко с полным перечнем компетенций
    def showCompWindow(self):
        self.w = SkillWindow()
        self.w.setLayout(self.w.layout)
        skills = list(default_world.sparql("""
                    prefix enu: <http://www.enu.kz/ontologies/curriculum#>
                   SELECT ?s
                   WHERE {
                   ?s a enu:Skill.
                   ?s rdfs:label ?l .
                      FILTER NOT EXISTS {
                        ?s enu:isPartOf ?x
                        }
                   }
                    ORDER BY ?s
            """))
        print(skills)
        comp_tree_view = QTreeView()
        self.w.layout.addWidget(comp_tree_view)
        comp_tree_model = QStandardItemModel()
        comp_tree_view.setModel(comp_tree_model)
        for skill in skills:
            parent = QStandardItem(skill[0].name + ' ' + skill[0].label[0])
            comp_tree_model.appendRow(self.get_skills(skill, 1, parent))
            comp_tree_view.show()
            self.w.show()

    def view_doubleClicked(self, index):
        self.prereqListWidget.clear()
        self.compListWidget.clear()
        item = self.treeView.selectedIndexes()[0]
        if index.parent().isValid(): # был выбран курс
            # Формируемые компетенции
            competencies = list(default_world.sparql("""
                              prefix enu: <http://www.enu.kz/ontologies/curriculum#>
                              SELECT ?cmp ?lcmp
                              WHERE {
                                  ?c enu:train ?cmp .
                                  ?cmp rdfs:label ?lcmp .
                                  ?c rdfs:label '""" + item.model().itemFromIndex(index).text() + """'
                              }
                               ORDER BY ?c
                       """))
            for c in competencies:
                self.compListWidget.addItem("{} {}".format(c[0].name, c[0].label[0]))
            # competency = QListWidget(item.model().itemFromIndex(index).text())

            # Требуемые компетенции

            prereq_competences = list(default_world.sparql("""
                                            prefix enu: <http://www.enu.kz/ontologies/curriculum#>
                                            SELECT DISTINCT ?q
                                            WHERE {
                                                 ?c enu:requires ?q
                                                 ?d enu:train ?c .
                                                ?d rdfs:label '""" + item.model().itemFromIndex(index).text() + """' 
                                               }
                                        """))
            for c in prereq_competences:
                self.prereqListWidget.addItem("{} {}".format(c[0].name, c[0].label[0]))

        else: # Был выбран семестр
            # Формируемые компетенции
            print(item.model().itemFromIndex(index).text())
            competencies = list(default_world.sparql("""
                                         prefix enu: <http://www.enu.kz/ontologies/curriculum#>
                                         SELECT ?cmp
                                         WHERE {
                                             
                                            ?c enu:train ?cmp
                                            ?c enu:train ?cmp
                                             ?c enu:studiedDuring ?s.
                                            ?s rdfs:label '""" + item.model().itemFromIndex(index).text() + """' 
                                         }
                                          ORDER BY ?c
                                  """))
            for c in competencies:
                self.compListWidget.addItem("{} {}".format(c[0].name, c[0].label[0]))
            # competency = QListWidget(item.model().itemFromIndex(index).text())

           # Требуемые компетенции

            prereq_competences = list(default_world.sparql("""
                                      prefix enu: <http://www.enu.kz/ontologies/curriculum#>
                                      SELECT DISTINCT ?q
                                      WHERE {
                                           ?c enu:requires ?q
                                           ?d enu:train ?c .
                                           ?d enu:studiedDuring ?s.
                                          ?s rdfs:label '""" + item.model().itemFromIndex(index).text() + """' 
                                         }
                                  """))
            for c in prereq_competences:
                self.prereqListWidget.addItem("{} {}".format(c[0].name, c[0].label[0]))



    def view_expandAll(self):
        print(self.expandFlag)
        if self.expandFlag == 0:
            self.treeView.expandAll()
            self.expandFlag = 1
            self.expandAllButton.setText('Свернуть')
        else:
            self.treeView.collapseAll()
            self.expandFlag = 0
            self.expandAllButton.setText('Раскрыть все')


    def toggle_reasoner(self):
        print('toggled')
        if self.toggleReasonerCheckBox.isChecked():
            sync_reasoner_pellet(infer_property_values=True, infer_data_property_values=True)
        else:
            self.loadOntolory("/Users/kda/Documents/Интеллектуальные информационные системы/Модель компетенций/competencies2.rdf")

    def loadOntolory(self, filePath):
        onto = get_ontology(filePath).load()
        # sync_reasoner_pellet(infer_property_values=True, infer_data_property_values=True)
        view = self.treeView
        # view.setSelectionBehavior(QAbstractItemView.SelectRows)
        model = QStandardItemModel()
        # model.setHorizontalHeaderLabels(['col1', 'col2', 'col3'])
        view.setModel(model)
        # view.setUniformRowHeights(True)
        # for i in range(3):
        #     parent1 = QStandardItem('sdfsdf')
        #     for j in range(3):
        #         child1 = QStandardItem('Child {}'.format(i * 3 + j))
        #         child2 = QStandardItem('row: {}, col: {}'.format(i, j + 1))
        #         child3 = QStandardItem('row: {}, col: {}'.format(i, j + 2))
        #         parent1.appendRow([child1, child2, child3])
        #         for j in range(3):
        #             child11 = QStandardItem('Child {}'.format(i * 3 + j))
        #             child22 = QStandardItem('row: {}, col: {}'.format(i, j + 1))
        #             child33 = QStandardItem('row: {}, col: {}'.format(i, j + 2))
        #             child1.appendRow([child11, child22, child33])
        #     model.appendRow(parent1)
        #     # span container columns
        #     view.setFirstColumnSpanned(i, view.rootIndex(), True)
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # expand third container
        # index = model.indexFromItem(parent1)
        # view.expand(index)
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # select last row
        # selmod = view.selectionModel()
        # index2 = model.indexFromItem(child3)
        # selmod.select(index2, QItemSelectionModel.Select | QItemSelectionModel.Rows)
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


        for semester in onto.Semester.instances():
            parent1 = QStandardItem(semester.label[0])
            courses = list(default_world.sparql("""
                               prefix enu: <http://www.enu.kz/ontologies/curriculum#>
                               SELECT DISTINCT ?d
                               WHERE {
                                    ?d enu:studiedDuring ?s.
                                   ?s rdfs:label '""" + semester.label[0] + """'
                                  }
                           """))
            childs = []
            for c in courses:
                childs.append(QStandardItem(c[0].label[0]))
                parent1.appendRow(QStandardItem(c[0].label[0]))
            model.appendRow(parent1)
            # print(childs)
            view.show()



    # def getCompetencies(self, top_competencies=None):
    #     if top_competencies is None:
    #         top_competencies = list(default_world.sparql("""
    #                    SELECT ?s ?l
    #                    WHERE {
    #                    ?s a <http://www.enu.kz/ontologies/curriculum#Skill>.
    #                    ?s rdfs:label ?l .
    #                       FILTER NOT EXISTS {
    #                         ?s <http://www.enu.kz/ontologies/curriculum#isPartOf> ?x
    #                         }
    #                    }
    #                     ORDER BY ?s
    #             """))
    #
    #
    #
    #     for competency in top_competencies:
    #         print(competency[0].name[6:], '. ', competency[1], sep='')
    #         self.get_skills(competency[1], 1)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyWidget()
    ex.show()
    sys.exit(app.exec_())