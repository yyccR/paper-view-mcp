import unittest
from unittest.mock import AsyncMock, patch

from integrations.mcp_server import server


class ImageToolTests(unittest.IsolatedAsyncioTestCase):
    async def test_quote_and_submit_forward_the_identical_inference_inputs(self):
        options = dict(model='gpt-image-2.5', image_size='2K', aspect_ratio='16:9',
                       generation_quality='high', reference_images=['https://cdn.test/ref.png'],
                       mask_image='https://cdn.test/mask.png',
                       model_parameters={'n': 2, 'background': 'transparent', 'size': '1536x1024'})
        with patch.object(server, '_api', new_callable=AsyncMock) as api:
            api.return_value = {'board_url': '/board?board_session=example&compact=1'}
            await server.quote_image(**options)
            quoted = api.call_args.kwargs['payload']
            await server.submit_image(prompt='Edit these cells', client_request_id='stable-request', **options)
            submitted = api.call_args.kwargs['payload']
        self.assertEqual(quoted, {key: submitted[key] for key in quoted})
        self.assertEqual(submitted['client_request_id'], 'stable-request')
        self.assertEqual(submitted['reference_images'], options['reference_images'])

    async def test_live_mcp_schema_exposes_reference_and_native_parameter_inputs(self):
        tools = {tool.name: tool for tool in await server.mcp.list_tools()}
        for name in ('quote_image', 'submit_image'):
            properties = tools[name].inputSchema['properties']
            for field in ('reference_images', 'mask_image', 'model_parameters'):
                self.assertIn(field, properties)
        self.assertIn('prompt', tools['submit_image'].inputSchema['required'])


if __name__ == '__main__':
    unittest.main()
