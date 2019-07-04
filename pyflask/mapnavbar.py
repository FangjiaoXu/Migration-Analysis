from jinja2 import Template
from branca.element import MacroElement
class FloatImage(MacroElement):
    """Adds a floating image in HTML canvas on top of the map."""
    _template = Template("""
            {% macro header(this,kwargs) %}
                <style>
                    #{{this.get_name()}} {
                        position:absolute;
                        top:0%;
                        left: 5%;}
                        </style> 
                                    
            {% endmacro %}
            {% macro html(this,kwargs) %}
            <div id="{{this.get_name()}}" style="font-color:'#000000'; z-index: 999999">
                 <a href="#" onclick="history.go(-1)"><h3>Back<h3></a>
            </div>

            {% endmacro %}
            """)

    def __init__(self):
        super(FloatImage, self).__init__()
        self._name = 'NavBar'