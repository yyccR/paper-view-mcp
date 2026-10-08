"""Local end-to-end smoke: draw a multi-layer EGFR signaling mechanism.

Set PAPER_VIEW_API_BASE_URL, PAPER_VIEW_PUBLIC_URL, and PAPER_VIEW_TEST_TOKEN_FILE.
This script calls the same MCP tool functions exposed to Codex and WorkBuddy.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import uuid
from pathlib import Path

from integrations.mcp_server import server


SVG_OPEN = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 800">'
SVG_CLOSE = '</svg>'


LAYERS = [
    ('Compartments and title', '''
<rect x="0" y="0" width="1200" height="800" fill="#f7f8f2"/>
<rect x="36" y="92" width="1128" height="146" rx="26" fill="#e8f2ed"/>
<rect x="36" y="260" width="1128" height="502" rx="30" fill="#fffdf8" stroke="#d9e2da" stroke-width="2"/>
<path d="M55 238 L1145 238 M55 248 L1145 248" stroke="#5a8c7b" stroke-width="5"/>
<ellipse cx="974" cy="553" rx="158" ry="147" fill="#e9f0f7" stroke="#8faabd" stroke-width="3"/>
<text x="54" y="54" fill="#183a36" font-family="Avenir Next" font-size="30" font-weight="700">EGFR signaling: growth and survival</text>
<text x="56" y="77" fill="#58706e" font-family="Avenir Next" font-size="15">An editable, five-layer mechanism diagram drawn incrementally by an MCP agent</text>
<text x="63" y="119" fill="#558378" font-family="Avenir Next" font-size="15" font-weight="700">EXTRACELLULAR SPACE</text>
<text x="65" y="294" fill="#7a8775" font-family="Avenir Next" font-size="15" font-weight="700">CYTOPLASM</text>
<text x="915" y="434" fill="#68859b" font-family="Avenir Next" font-size="16" font-weight="700">NUCLEUS</text>
<text x="60" y="785" fill="#728480" font-family="Avenir Next" font-size="13">Solid arrows: activation  /  Red dashed lines: feedback inhibition</text>
'''),
    ('Ligand and receptor activation', '''
<defs><marker id="arrow-a" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto"><path d="M0 0 L10 5 L0 10" fill="#2e766c"/></marker></defs>
<circle cx="244" cy="160" r="28" fill="#f5cf83" stroke="#bd8e3e" stroke-width="3"/>
<circle cx="278" cy="151" r="24" fill="#f5cf83" stroke="#bd8e3e" stroke-width="3"/>
<text x="270" y="116" fill="#825f31" font-family="Avenir Next" font-size="17" font-weight="700">EGF ligand</text>
<path d="M281 173 C310 188 335 190 358 202" fill="none" stroke="#2e766c" stroke-width="4" marker-end="url(#arrow-a)"/>
<path d="M375 201 C364 185 352 180 338 190 C330 203 337 218 365 225 L365 287 L388 287 L388 224 C411 213 419 201 409 190 C395 180 386 187 375 201 Z" fill="#f5d5bf" stroke="#aa6848" stroke-width="3"/>
<path d="M423 201 C412 185 400 180 386 190 C378 203 385 218 413 225 L413 287 L436 287 L436 224 C459 213 467 201 457 190 C443 180 434 187 423 201 Z" fill="#f5d5bf" stroke="#aa6848" stroke-width="3"/>
<circle cx="379" cy="296" r="7" fill="#e3a03e"/><circle cx="423" cy="296" r="7" fill="#e3a03e"/>
<text x="474" y="186" fill="#8a543d" font-family="Avenir Next" font-size="18" font-weight="700">EGFR dimer</text>
<text x="474" y="209" fill="#aa6848" font-family="Avenir Next" font-size="13">Autophosphorylation</text>
<path d="M401 300 L401 329" fill="none" stroke="#2e766c" stroke-width="4" marker-end="url(#arrow-a)"/>
<rect x="341" y="334" width="120" height="48" rx="23" fill="#d9eee7" stroke="#4e9684" stroke-width="2"/>
<text x="366" y="364" fill="#245d55" font-family="Avenir Next" font-size="17" font-weight="700">GRB2 / SOS</text>
'''),
    ('MAPK cascade', '''
<defs><marker id="arrow-m" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto"><path d="M0 0 L10 5 L0 10" fill="#2e766c"/></marker></defs>
<path d="M402 385 L402 412 M402 467 L402 493 M402 548 L402 574 M478 622 C606 631 688 618 791 581" fill="none" stroke="#2e766c" stroke-width="4" marker-end="url(#arrow-m)"/>
<rect x="340" y="417" width="124" height="50" rx="25" fill="#e6dbf0" stroke="#8971a2" stroke-width="3"/>
<text x="377" y="448" fill="#614477" font-family="Avenir Next" font-size="20" font-weight="700">RAS</text>
<rect x="340" y="497" width="124" height="50" rx="25" fill="#e6dbf0" stroke="#8971a2" stroke-width="3"/>
<text x="377" y="528" fill="#614477" font-family="Avenir Next" font-size="20" font-weight="700">RAF</text>
<rect x="340" y="578" width="124" height="50" rx="25" fill="#e6dbf0" stroke="#8971a2" stroke-width="3"/>
<text x="376" y="609" fill="#614477" font-family="Avenir Next" font-size="20" font-weight="700">MEK</text>
<rect x="340" y="658" width="124" height="50" rx="25" fill="#e6dbf0" stroke="#8971a2" stroke-width="3"/>
<text x="375" y="689" fill="#614477" font-family="Avenir Next" font-size="20" font-weight="700">ERK</text>
<text x="70" y="478" fill="#817095" font-family="Avenir Next" font-size="14">MAPK phosphorylation cascade</text>
<path d="M402 629 L402 653" fill="none" stroke="#2e766c" stroke-width="4" marker-end="url(#arrow-m)"/>
<path d="M471 680 C635 716 754 673 835 613" fill="none" stroke="#2e766c" stroke-width="4" marker-end="url(#arrow-m)"/>
'''),
    ('PI3K and AKT survival branch', '''
<defs><marker id="arrow-p" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto"><path d="M0 0 L10 5 L0 10" fill="#2e766c"/></marker></defs>
<path d="M451 361 C555 355 608 361 651 392" fill="none" stroke="#2e766c" stroke-width="4" marker-end="url(#arrow-p)"/>
<rect x="652" y="372" width="130" height="54" rx="26" fill="#dfece5" stroke="#669574" stroke-width="3"/>
<text x="689" y="406" fill="#396d4b" font-family="Avenir Next" font-size="20" font-weight="700">PI3K</text>
<path d="M717 430 L717 469" fill="none" stroke="#2e766c" stroke-width="4" marker-end="url(#arrow-p)"/>
<rect x="652" y="474" width="130" height="54" rx="26" fill="#dfece5" stroke="#669574" stroke-width="3"/>
<text x="686" y="508" fill="#396d4b" font-family="Avenir Next" font-size="20" font-weight="700">PIP3</text>
<path d="M717 532 L717 570" fill="none" stroke="#2e766c" stroke-width="4" marker-end="url(#arrow-p)"/>
<rect x="652" y="575" width="130" height="54" rx="26" fill="#dfece5" stroke="#669574" stroke-width="3"/>
<text x="692" y="609" fill="#396d4b" font-family="Avenir Next" font-size="20" font-weight="700">AKT</text>
<path d="M717 633 L717 669" fill="none" stroke="#2e766c" stroke-width="4" marker-end="url(#arrow-p)"/>
<rect x="637" y="675" width="160" height="54" rx="26" fill="#dfece5" stroke="#669574" stroke-width="3"/>
<text x="668" y="709" fill="#396d4b" font-family="Avenir Next" font-size="19" font-weight="700">mTORC1</text>
<text x="654" y="348" fill="#60916f" font-family="Avenir Next" font-size="15" font-weight="700">SURVIVAL BRANCH</text>
'''),
    ('Transcription and negative feedback', '''
<defs><marker id="arrow-f" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto"><path d="M0 0 L10 5 L0 10" fill="#2e766c"/></marker></defs>
<rect x="878" y="478" width="190" height="58" rx="20" fill="#ffffff" stroke="#93adbf" stroke-width="2"/>
<text x="911" y="504" fill="#42637b" font-family="Avenir Next" font-size="19" font-weight="700">ELK1 / FOS</text>
<text x="921" y="524" fill="#647f91" font-family="Avenir Next" font-size="13">Transcription factors</text>
<path d="M974 540 L974 566" fill="none" stroke="#2e766c" stroke-width="4" marker-end="url(#arrow-f)"/>
<rect x="874" y="571" width="199" height="82" rx="20" fill="#dce9f1" stroke="#8aa7bb" stroke-width="2"/>
<text x="895" y="601" fill="#385d77" font-family="Avenir Next" font-size="18" font-weight="700">Growth programs</text>
<text x="892" y="626" fill="#5f7c8c" font-family="Avenir Next" font-size="14">Proliferation / survival</text>
<path d="M868 674 C757 762 570 754 479 704" fill="none" stroke="#be6d62" stroke-width="3" stroke-dasharray="9 7"/>
<rect x="470" y="728" width="128" height="27" rx="13" fill="#f4ded8"/>
<text x="482" y="747" fill="#a75c52" font-family="Avenir Next" font-size="13" font-weight="700">DUSP6 inhibits ERK</text>
<path d="M875 466 C790 311 606 317 463 351" fill="none" stroke="#be6d62" stroke-width="3" stroke-dasharray="9 7"/>
<rect x="568" y="294" width="172" height="27" rx="13" fill="#f4ded8"/>
<text x="584" y="313" fill="#a75c52" font-family="Avenir Next" font-size="13" font-weight="700">SPRY inhibits adaptor</text>
'''),
]


async def draw(output_path: Path) -> None:
    session = await server.start_drawing('EGFR signaling mechanism - editable SVG')
    results = []
    for title, content in LAYERS:
        result = await server.draw_svg_layer(
            session['session_id'], title, SVG_OPEN + content + SVG_CLOSE,
            str(uuid.uuid4()),
        )
        results.append(result)
        status = await server.inspect_drawing(session['session_id'])
        print(f'{title}: revision {result["revision"]}, {len(status["layers"])} saved layers')
    output_path.write_text(json.dumps({
        'session_id': session['session_id'],
        'board_url': session['board_url'],
        'layers': results,
    }, indent=2), encoding='utf-8')
    print(f'Board: {session["board_url"]}')


async def update(output_path: Path) -> None:
    data = json.loads(output_path.read_text(encoding='utf-8'))
    last = data['layers'][-1]
    layer = await server.get_svg_layer(last['artifact_ref'])
    revised = layer['svg_text'].replace('Growth programs', 'Growth response')
    result = await server.update_svg_layer(
        data['session_id'], last['artifact_ref'], layer['revision'],
        'Transcription and negative feedback', revised, str(uuid.uuid4()),
    )
    print(f'Updated {result["artifact_ref"]} to revision {result["revision"]}')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['draw', 'update'])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    token_file = Path(os.environ['PAPER_VIEW_TEST_TOKEN_FILE'])
    token = token_file.read_text(encoding='utf-8').strip()
    server._auth_header = lambda: {'Authorization': f'Bearer {token}'}
    asyncio.run(draw(args.output) if args.command == 'draw' else update(args.output))


if __name__ == '__main__':
    main()
