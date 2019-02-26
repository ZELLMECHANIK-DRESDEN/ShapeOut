from docutils import nodes
from docutils.statemachine import ViewList
from docutils.parsers.rst import Directive
import importlib.util
from sphinx.util.nodes import nested_parse_with_titles

import pathlib

import dclab

here = pathlib.Path(__file__).resolve().parent
root = here.parent.parent
proot = root / "shapeout"


class ExpertFeatures(Directive):
    def run(self):
        spath = proot / "settings.py"
        spec = importlib.util.spec_from_file_location("settings", str(spath))
        sett = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sett)

        rst = []
        for ft in sett.EXPERT_FEATURES:
            rst.append(" - {} (``{}``)".format(
                dclab.dfn.feature_name2label[ft], ft))

        vl = ViewList(rst, "fakefile.rst")
        # Create a node.
        node = nodes.section()
        node.document = self.state.document
        # Parse the rst.
        nested_parse_with_titles(self.state, vl, node)
        return node.children


def setup(app):
    app.add_directive("so_expert_features", ExpertFeatures)
