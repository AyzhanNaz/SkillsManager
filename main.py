from PyQt5.QtChart import QBarSet, QBarSeries, QChart, QBarCategoryAxis, QValueAxis, QChartView
from owlready2 import *
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPainter
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeView, QWidget, QVBoxLayout


class SkillWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Curriculum competencies")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setGeometry(300, 300, 600, 600)

class ChartWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Curriculum analysis")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setGeometry(300, 300, 1200, 600)

class MyWidget(QMainWindow):
    expandFlag = 0 # Course List Expansion State
    def __init__(self):
        super().__init__()
        uic.loadUi('skillmanager.ui', self)
        self.initUI()
        self.loadOntology("competencies2.rdf")

    def initUI(self):
        self.treeView.clicked.connect(self.view_doubleClicked)
        self.expandAllButton.clicked.connect(self.view_expandAll)
        self.showCompButton.clicked.connect(self.showCompWindow)
        self.showChartButton.clicked.connect(self.showCurriculumChart)
        self.toggleReasonerCheckBox.stateChanged.connect(self.toggle_reasoner)

    def closeEvent(self, event):
        for window in QApplication.topLevelWidgets():
            window.close()

    # Get list of top-level skills
    def get_top_skills(self):
        skills = list(default_world.sparql("""
            prefix enu: <http://www.enu.kz/ontologies/curriculum#>
            SELECT ?s ?l
            WHERE {
                ?s a enu:Skill .
                ?s rdfs:label ?l .
                FILTER(LANG(?l) = "" || LANGMATCHES(LANG(?l), "en")).
                FILTER NOT EXISTS {
                    ?s enu:isPartOf ?x
                }
            }
            ORDER BY ?s
        """))
        return skills

    # Recursive function for obtaining child competencies
    def get_skills(self, skill, i, parent):
        skills = list(default_world.sparql("""
            prefix enu: <http://www.enu.kz/ontologies/curriculum#>
            SELECT ?s ?l
            WHERE {
               ?s enu:isPartOf ?x.
               ?s rdfs:label ?l.
               FILTER(LANG(?l) = "" || LANGMATCHES(LANG(?l), "en")).
                ?x rdfs:label '""" + skill[0].label[0] + """'
            }
            ORDER BY ?s
        """))
        i += 1
        for skill in skills:
            child = QStandardItem(skill[0].name + ' ' + skill[1])
            parent.appendRow(self.get_skills(skill, i, child))
        return parent

    # Chart plot
    def showCurriculumChart(self):
        self.set0 = QBarSet("Previously acquired competencies")
        self.set1 = QBarSet("Required competencies")
        self.set2 = QBarSet("Lack of competence")
        self.set0.append(list(map(lambda x: len(self.get_prev_trained_skills_by_semester_name(x.label[0])), self.onto.Semester.instances())))
        self.set1.append(list(map(lambda x: len(self.get_required_skills_by_semester_name(x.label[0])), self.onto.Semester.instances())))
        self.set2.append(list(map(lambda x: len(set(map(lambda y: y[0].name, self.get_required_skills_by_semester_name(x.label[0]))) - set(map(lambda z: z[0].name, self.get_prev_trained_skills_by_semester_name(x.label[0])))), self.onto.Semester.instances())))

        self._bar_series = QBarSeries()
        self._bar_series.append(self.set0)
        self._bar_series.append(self.set1)
        self._bar_series.append(self.set2)

        self.chart = QChart()
        self.chart.addSeries(self._bar_series)
        # self.chart.addSeries(self._line_series)
        self.chart.setTitle("Curriculum competense analyzing")

        self.categories = list(map(lambda x: x.label[0][9:11], self.onto.Semester.instances()))
        self._axis_x = QBarCategoryAxis()
        self._axis_x.append(self.categories)
        self.chart.addAxis(self._axis_x, Qt.AlignBottom)
        # self._line_series.attachAxis(self._axis_x)
        self._bar_series.attachAxis(self._axis_x)
        self._axis_x.setRange("Jan", "Jun")

        self._axis_y = QValueAxis()
        self.chart.addAxis(self._axis_y, Qt.AlignLeft)
        # self._line_series.attachAxis(self._axis_y)
        self._bar_series.attachAxis(self._axis_y)
        self._axis_y.setRange(0, 200)

        # self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignBottom)

        self._chart_view = QChartView(self.chart)
        self._chart_view.setRenderHint(QPainter.Antialiasing)
        self._axis_x.setTitleText("Semester")
        self._axis_y.setTitleText("Number of Competencies")

        # self.setCentralWidget(self._chart_view)
        self.w = ChartWindow()
        self.w.setLayout(self.w.layout)
        self.w.layout.addWidget(self._chart_view)
        self._chart_view.show()
        self.w.show()

    # Window with a complete list of competencies
    def showCompWindow(self):
        self.w = SkillWindow()
        self.w.setLayout(self.w.layout)
        # Get list of top-level skills
        skills = self.get_top_skills()
        comp_tree_view = QTreeView()
        self.w.layout.addWidget(comp_tree_view)
        comp_tree_model = QStandardItemModel()
        comp_tree_model.setHorizontalHeaderLabels(['Competency model'])
        comp_tree_view.setModel(comp_tree_model)
        for skill in skills:
            parent = QStandardItem(skill[0].name + ' ' + skill[1])
            comp_tree_model.appendRow(self.get_skills(skill, 1, parent))
            print(skill)
        comp_tree_view.show()
        self.w.show()

    def get_trained_skills_by_course_name(self, course_name):
        return list(default_world.sparql("""
                                      prefix enu: <http://www.enu.kz/ontologies/curriculum#>
                                      SELECT DISTINCT ?cmp ?lcmp
                                      WHERE {
                                          ?c enu:train ?cmp .
                                          ?cmp rdfs:label ?lcmp .
                                          FILTER(LANG(?lcmp) = "" || LANGMATCHES(LANG(?lcmp), "en")).
                                          ?c rdfs:label '""" + course_name + """'
                                      }
                                       ORDER BY ?cmp
                               """))

    def get_prev_trained_skills_by_course_name(self, course_name):
        return list(default_world.sparql("""
                prefix enu: <http://www.enu.kz/ontologies/curriculum#>
                SELECT ?cmp ?lcmp
                WHERE {
                    ?cmp rdfs:label ?lcmp .
                    ?d enu:train ?cmp .
                    ?d enu:studiedDuring ?p.
                    ?p enu:goesBefore ?s . 
                    ?c enu:studiedDuring ?s.
                    FILTER(LANG(?lcmp) = "" || LANGMATCHES(LANG(?lcmp), "en")).
                    ?c rdfs:label '""" + course_name + """'
                    }
                ORDER BY ?cmp
        """))


    def get_required_skills_by_course_name(self, course_name):
        return list(default_world.sparql("""
                                            prefix enu: <http://www.enu.kz/ontologies/curriculum#>
                                            SELECT DISTINCT ?q ?lcmp
                                            WHERE {
                                                 ?c enu:requires ?q
                                                 ?d enu:train ?c .
                                                 ?q rdfs:label ?lcmp .
                                                 FILTER(LANG(?lcmp) = "" || LANGMATCHES(LANG(?lcmp), "en")).
                                                ?d rdfs:label '""" + course_name + """' 
                                               }
                                        """))

    # Competencies developed by studying all courses of PREVIOUS semesters
    def get_prev_trained_skills_by_semester_name(self, semester_name):
        return list(default_world.sparql("""
                                         prefix enu: <http://www.enu.kz/ontologies/curriculum#>
                                         SELECT ?cmp ?lcmp
                                         WHERE {
                                            ?c enu:train ?cmp .
                                             ?c enu:studiedDuring ?p.
                                             ?p enu:goesBefore ?s .
                                             ?cmp rdfs:label ?lcmp .
                                              FILTER(LANG(?lcmp) = "" || LANGMATCHES(LANG(?lcmp), "en")).
                                            ?s rdfs:label '""" + semester_name + """' 
                                         }
                                          ORDER BY ?c
                                  """))

    def get_required_skills_by_semester_name(self, semester_name):
        return list(default_world.sparql("""
                                      prefix enu: <http://www.enu.kz/ontologies/curriculum#>
                                      SELECT DISTINCT ?q ?lcmp
                                      WHERE {
                                           ?c enu:requires ?q
                                           ?d enu:train ?c .
                                           ?d enu:studiedDuring ?s.
                                            ?q rdfs:label ?lcmp .
                                           FILTER(LANG(?lcmp) = "" || LANGMATCHES(LANG(?lcmp), "en")).
                                          ?s rdfs:label '""" + semester_name + """' 
                                         }
                                  """))

    def view_doubleClicked(self, index):
        self.prereqListWidget.clear()
        self.compListWidget.clear()
        self.lackSkillsListWidget.clear()
        item = self.treeView.selectedIndexes()[0]
        if index.parent().isValid():
            # course has been selected
            self.label_5.setText("Selected course: " + item.model().itemFromIndex(index).text())
            self.label.setText("Competencies developed by the course")
            self.label_2.setText("Competencies required to study the course")
            self.label_3.setText("Competencies insufficient to study the course")
            self.label_3.setStyleSheet("color: red")
            # Competencies developed by the course
            trained_skills = self.get_trained_skills_by_course_name(item.model().itemFromIndex(index).text())
            print(item.model().itemFromIndex(index).text())
            for skill in trained_skills:
                self.compListWidget.addItem("{} {}".format(skill[0].name, skill[1]))
            # Required competencies
            required_skills = self.get_required_skills_by_course_name(item.model().itemFromIndex(index).text())
            for required_skill in required_skills:
                self.prereqListWidget.addItem("{} {}".format(required_skill[0].name, required_skill[1]))
            # Компетенции формируемые всеми предыдущими семестрами
            prev_trained_skills = self.get_prev_trained_skills_by_semester_name(item.model().itemFromIndex(index.parent()).text())
            for skill in required_skills:
                if skill not in prev_trained_skills:
                    self.lackSkillsListWidget.addItem("{} {}".format(skill[0].name, skill[1]))
        else:
            # semester has been selected
            self.label_5.setText("Selected semester: " + item.model().itemFromIndex(index).text())
            self.label.setText("Competencies developed by all courses \n of PREVIOUS semesters")
            self.label_2.setText("Competencies required to complete all semester courses")
            self.label_3.setText("Competencies insufficient to study all courses of the semester")
            self.label_3.setStyleSheet("color: red")
            # Формируемые компетенции
            prev_trained_skills = self.get_prev_trained_skills_by_semester_name(item.model().itemFromIndex(index).text())
            for skill in prev_trained_skills:
                self.compListWidget.addItem("{} {}".format(skill[0].name, skill[1]))
           # Требуемые компетенции
            required_skills = self.get_required_skills_by_semester_name(item.model().itemFromIndex(index).text())
            for skill in required_skills:
                self.prereqListWidget.addItem("{} {}".format(skill[0].name, skill[1]))
            for skill in required_skills:
                if skill not in prev_trained_skills:
                    self.lackSkillsListWidget.addItem("{} {}".format(skill[0].name, skill[1]))

    def view_expandAll(self):
        print(self.expandFlag)
        if self.expandFlag == 0:
            self.treeView.expandAll()
            self.expandFlag = 1
            self.expandAllButton.setText('Collapse All')
        else:
            self.treeView.collapseAll()
            self.expandFlag = 0
            self.expandAllButton.setText('Expand All')



    def toggle_reasoner(self):
        if self.toggleReasonerCheckBox.isChecked():
            sync_reasoner(infer_property_values=True)
        else:
            self.loadOntology("/Users/kda/Documents/Интеллектуальные информационные системы/Модель компетенций/Competencies2.rdf")

    def loadOntology(self, filePath):
        self.onto = get_ontology(filePath).load()
        # sync_reasoner_pellet(infer_property_values=True, infer_data_property_values=True)
        view = self.treeView
        # view.setSelectionBehavior(QAbstractItemView.SelectRows)
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(['Courses by semester'])
        view.setModel(model)
        # view.setHeaderHidden(True)

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


        for semester in self.onto.Semester.instances():
            print(semester.label[0])
            parent = QStandardItem(semester.label[0])
            courses = list(default_world.sparql("""
                               prefix enu: <http://www.enu.kz/ontologies/curriculum#>
                               SELECT DISTINCT ?d ?l
                               WHERE {
                                    ?d enu:studiedDuring ?s.
                                    ?d rdfs:label ?l.
                                    FILTER(LANG(?l) = "" || LANGMATCHES(LANG(?l), "en")).
                                   ?s rdfs:label '""" + semester.label[0] + """'
                                  }
                           """))
            for c in courses:
                 parent.appendRow(QStandardItem(c[1]))
            model.appendRow(parent)
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