import json
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView

class GraphView(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.browser = QWebEngineView()
        self.layout.addWidget(self.browser)

    def render_graph(self, nodes, edges):
        html_content = f"""
        <!DOCTYPE html>
        <html><head><meta charset="utf-8"><script src="https://cdn.jsdelivr.net/npm/echarts/dist/echarts.min.js"></script>
        <style>html, body, #main {{ width: 100%; height: 100%; margin: 0; padding: 0; background-color: #fafafa; }}</style></head>
        <body><div id="main"></div><script>
        var chart = echarts.init(document.getElementById('main'));
        var option = {{ tooltip: {{ formatter: '{{b}}' }}, series: [{{ type: 'graph', layout: 'force', roam: true, draggable: true,
        label: {{ show: true, position: 'right', formatter: '{{b}}', color: '#555' }}, force: {{ repulsion: 400, edgeLength: 100 }},
        data: {json.dumps(nodes)}, links: {json.dumps(edges)}, itemStyle: {{ color: '#8b5cf6', borderColor: '#fff', borderWidth: 2 }},
        lineStyle: {{ color: '#ccc', width: 2, curveness: 0.1 }} }}] }}; chart.setOption(option);
        </script></body></html>
        """
        self.browser.setHtml(html_content)
