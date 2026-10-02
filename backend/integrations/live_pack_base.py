"""Shared plumbing for packs whose actions are live buttons (DL-145).

Not named ``*_pack``: PluginManager only registers modules with that suffix,
so this helper is never mistaken for a pack itself.
"""
from typing import Any, Dict, List, Optional

from plugins.base_plugin import BasePlugin


def live_result(message: str, badge: str, status: str = 'normal',
                sublabel: str = '', menu: Optional[List[Dict[str, Any]]] = None,
                panel_text: Optional[str] = None,
                success: bool = True) -> Dict[str, Any]:
    """An action result that paints the button face.

    ``badge``/``status``/``sublabel`` are read by ``buttonState.markFinished``;
    ``menu`` and ``panel_text`` feed the press-menu sheet.
    """
    data: Dict[str, Any] = {'badge': badge, 'status': status}
    if sublabel:
        data['sublabel'] = sublabel
    if menu is not None:
        data['menu'] = menu
    if panel_text:
        data['panel_text'] = panel_text
    return {'success': success, 'message': message, 'data': data}


class SpecPlugin(BasePlugin):
    """A plugin whose schema is derived from its ``get_action_specs``."""

    def initialize(self) -> bool:
        return True

    def cleanup(self) -> None:
        pass

    def get_action_schema(self, action_id: str) -> Dict[str, Any]:
        for spec in self.get_action_specs() or ():
            if spec.id == action_id:
                return {
                    'type': 'object',
                    'properties': {
                        f.name: {'type': 'string', 'title': f.label}
                        for f in spec.config_fields
                    },
                    'required': [f.name for f in spec.config_fields
                                 if f.required],
                }
        return {}
