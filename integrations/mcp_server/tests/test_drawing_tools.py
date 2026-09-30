import unittest
from unittest.mock import AsyncMock, patch

from integrations.mcp_server import server


class DrawingToolTests(unittest.IsolatedAsyncioTestCase):
    async def test_start_drawing_creates_plugin_session(self):
        with patch.object(server, '_api', new_callable=AsyncMock) as api:
            api.return_value = {'id': '01a0f1a0-af60-7902-9490-33de2829b9f7', 'title': 'Mechanism'}
            result = await server.start_drawing('Mechanism')
        self.assertEqual(result['session_id'], '01a0f1a0-af60-7902-9490-33de2829b9f7')
        self.assertTrue(result['board_url'].endswith('compact=1'))
        self.assertTrue(api.call_args.kwargs['payload']['client_board_id'].startswith('plugin-'))

    async def test_layer_tools_keep_session_and_revision(self):
        session_id = '01a0f1a0-af60-7902-9490-33de2829b9f7'
        svg = '<svg viewBox="0 0 1200 800"><text x="10" y="20">MAPK</text></svg>'
        with patch.object(server, '_api', new_callable=AsyncMock) as api:
            api.return_value = {
                'session_id': session_id, 'artifact_ref': 'svg:layer-1',
                'revision': 1, 'board_url': f'/board?board_session={session_id}&compact=1',
            }
            added = await server.draw_svg_layer(session_id, 'Signals', svg, 'retry-1')
            self.assertEqual(api.call_args.kwargs['payload']['client_request_id'], 'retry-1')
            self.assertEqual(api.call_args.kwargs['payload']['svg_text'], svg)
            self.assertTrue(added['board_url'].startswith('https://ipaperview.com/'))

            api.return_value['revision'] = 2
            updated = await server.update_svg_layer(
                session_id, 'svg:layer-1', 1, 'Signals', svg, 'retry-2',
            )
            self.assertEqual(updated['revision'], 2)
            self.assertEqual(api.call_args.kwargs['payload']['base_revision'], 1)
            self.assertEqual(api.call_args.kwargs['payload']['artifact_ref'], 'svg:layer-1')

    async def test_inspect_and_read_layer(self):
        session_id = '01a0f1a0-af60-7902-9490-33de2829b9f7'
        with patch.object(server, '_api', new_callable=AsyncMock) as api:
            api.side_effect = [
                {'title': 'Mechanism', 'canvas_revision': 3},
                {'items': [{'artifact_ref': 'svg:layer-1', 'latest_revision': 2}]},
                {'svg_content': '<svg/>'},
            ]
            result = await server.inspect_drawing(session_id, include_canvas_svg=True)
            self.assertEqual(result['canvas_revision'], 3)
            self.assertEqual(result['canvas_svg'], '<svg/>')
            self.assertEqual(result['layers'][0]['latest_revision'], 2)

        with patch.object(server, '_api', new_callable=AsyncMock) as api:
            api.side_effect = [
                {'kind': 'svg', 'latest_revision': 2, 'title': 'Signals', 'origin_session_id': session_id},
                {'document': {'payload': {'svg_text': '<svg viewBox="0 0 1200 800"/>'}}},
            ]
            layer = await server.get_svg_layer('svg:layer-1')
            self.assertEqual(layer['revision'], 2)
            self.assertIn('<svg', layer['svg_text'])


if __name__ == '__main__':
    unittest.main()
