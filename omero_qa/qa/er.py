import yapgvb
from django.db.models.fields.related import OneToOneRel, ManyToManyRel, ManyToOneRel

class Diagram:
    _graph = None
    _models = []
    _relationships = []
    _is_built = False

    def __init__(self, title='Django Model ERD'):
        self._graph = yapgvb.Digraph(title)

    def get_graph(self):
        return self._graph;

    def add_model(self, model):
        self._models.append(model)

        # get relationships
        for field in model._meta.fields:
            if field.rel:
                self.add_relationship(model, field)
        
        # m2m relationships
        for field in model._meta.local_many_to_many:
            self.add_relationship(model, field)

    def remove_model(self, model):
        try:
            del self._models[model]
        except IndexError:
            pass

    def add_relationship(self, model, field):
        self._relationships.append((model,field))

    def render(self, format='png', engine='dot'):
        self._build()
        self._graph.layout(engine)
        file = '/tmp/graph.%s' % format
        self._graph.render(file, format=format)
        content = open(file, 'r').read()
        import os; os.remove(file)
        return content

   
    def _build(self):
        if self._is_built:
            return
    
        nodes = {}
        for model in self._models:
            name = model.__name__
            label = model.__name__
            nodes[name] = self._graph.add_node(name, label=label, shape='record')
        
        for model, field in self._relationships:
            if nodes.get(field.rel.to.__name__):
                edge = self._graph.add_edge(nodes.get(model.__name__), nodes.get(field.rel.to.__name__))
                edge.arrowhead, edge.arrowtail = self._get_arrow(model, field)
                edge.minlen = 2


    def _get_arrow(self, model, field):
        map = {
            'many'     : 'crow',
            'one'      : 'tee',
            'required' : 'tee',
            'optional' : 'odot',
        }
        
        # get cardinality and modality
        if type(field.rel) == OneToOneRel:
            cardinality = ('one', 'one')
            
        elif type(field.rel) == ManyToOneRel:
            cardinality = ('one', 'many')

        elif type(field.rel) == ManyToManyRel:
            cardinality = ('many', 'many')
    
        
        # :KLUDGE: we're just guessing the most likely case for modality here
        if field.blank or type(field.rel) == ManyToManyRel:
            modality = ('optional', 'optional')
        else:
            modality = ('required', 'optional')

        return (map[cardinality[0]] + map[modality[0]],
                map[cardinality[1]] + map[modality[1]])

