import os
import re
from collections import defaultdict
from graphviz import Digraph

def map_file_relationships(folder_path):
    relationships = defaultdict(list)
    import_pattern = re.compile(r'from\s+(\S+)\s+import|import\s+(\S+)')

    for filename in os.listdir(folder_path):
        if filename.endswith('.py'):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r') as file:
                content = file.read()
                imports = import_pattern.findall(content)
                imported_modules = set(sum(imports, ()))

                for module in imported_modules:
                    module_file = module + '.py'
                    if module and module_file in os.listdir(folder_path):
                        relationships[filename].append(module_file)

    return relationships

def create_flowchart(relationships, output_file, height=10, width=10):
    dot = Digraph(comment='Python File Relationships')

     # Set graph attributes for height and width
    dot.graph_attr.update(size=f"{width},{height}!", rankdir='LR')

    # Add nodes
    for file in relationships:
        dot.node(file, file)

    # Add edges
    for file, imports in relationships.items():
        for imported_file in imports:
            dot.edge(file, imported_file)

    # Render the diagram to a file
    dot.render(output_file, format='png', cleanup=True)
    print(f"Flowchart saved as {output_file}.png")

# Set the path to the folder containing your bot's .py files
folder_path = 'C:/Users/Carlos/Dropbox/Artificial Intelligence/FOREX/BotNitoTrading/'

# Map the relationships
relationships = map_file_relationships(folder_path)

# Create a flowchart
output_file = 'bot_components'
create_flowchart(relationships, output_file, height=15, width=25)
