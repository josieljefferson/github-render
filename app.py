from flask import Flask, Response
import os
import json
from epg import generate_epg

app = Flask(__name__)

RAILWAY_PROXY = os.environ.get("PROXY_URL", "http://localhost:3000")

# Carregar canais do arquivo JSON
def load_channels():
    try:
        with open('channels.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('channels', [])
    except FileNotFoundError:
        print("Arquivo channels.json não encontrado. Usando canais padrão.")
        return []
    except json.JSONDecodeError:
        print("Erro ao decodificar channels.json. Usando canais padrão.")
        return []

# Converter os canais do JSON para o formato usado no app
def get_channels():
    channels_json = load_channels()
    channels_dict = {}
    
    for channel in channels_json:
        # Usar o ID como chave, garantindo unicidade
        channel_id = channel.get('id', '')
        if not channel_id:
            continue
            
        # Formatar o stream URL
        if RAILWAY_PROXY and 'http' in RAILWAY_PROXY:
            # Se tiver PROXY_URL, usá-lo para criar HLS
            stream_url = f"{RAILWAY_PROXY}/hls/{channel_id}"
        else:
            # Usar URL direta do JSON
            stream_url = channel.get('url', '')
        
        channels_dict[channel_id] = {
            "name": channel.get('tvg-name', channel.get('name', '')),
            "group": channel.get('group-title', ''),
            "logo": channel.get('tvg-logo', ''),
            "stream": stream_url,
            "tvg_id": channel.get('tvg-id', ''),
            "original_url": channel.get('url', '')
        }
    
    return channels_dict

@app.route("/")
def index():
    return "<h1>Servidor IPTV Online</h1>"

@app.route("/playlist.m3u")
def playlist():
    channels = get_channels()
    base = os.environ.get("RENDER_EXTERNAL_URL", "http://localhost:8080")
#    m3u = "#EXTM3U\n"
    m3u = """#EXTM3U url-tvg="https://m3u4u.com/epg/jq2zy9epr3bwxmgwyxr5, https://m3u4u.com/epg/3wk1y24kx7uzdevxygz7, https://m3u4u.com/epg/782dyqdrqkh1xegen4zp, https://www.open-epg.com/files/brazil1.xml.gz, https://www.open-epg.com/files/brazil2.xml.gz, https://www.open-epg.com/files/brazil3.xml.gz, https://www.open-epg.com/files/brazil4.xml.gz, https://www.open-epg.com/files/portugal1.xml.gz, https://www.open-epg.com/files/portugal2.xml.gz, https://epgshare01.online/epgshare01/epg_ripper_BR1.xml.gz, https://epgshare01.online/epgshare01/epg_ripper_PT1.xml.gz"

#PLAYLISTV: pltv-logo="https://cdn-icons-png.flaticon.com/256/25/25231.png" pltv-name="☆Josiel Jefferson☆" pltv-description="Playlist GitLab And GitHub Pages" pltv-cover="https://images.icon-icons.com/2407/PNG/512/gitlab_icon_146171.png" pltv-author="☆Josiel Jefferson☆" pltv-site="https://josieljefferson12.github.io/josieljefferson12.github.io.oficial" pltv-email="josielluz@proton.me"
"""

    for channel_id, channel in channels.items():
        m3u += (
            f'#EXTINF:-1 tvg-id="{channel.get("tvg_id", channel_id)}" '
            f'tvg-name="{channel["name"]}" '
            f'tvg-logo="{channel["logo"]}" '
            f'group-title="{channel["group"]}",{channel["name"]}\n'
            f'{channel["stream"]}\n'
        )

    return Response(m3u, mimetype="audio/x-mpegurl")

@app.route("/playlist_raw.m3u")
def playlist_raw():
    """Retorna playlist com URLs originais (sem proxy)"""
    channels = load_channels()
    m3u = "#EXTM3U\n"

    for channel in channels:
        m3u += (
            f'#EXTINF:-1 tvg-id="{channel.get("tvg-id", "")}" '
            f'tvg-name="{channel.get("tvg-name", channel.get("name", ""))}" '
            f'tvg-logo="{channel.get("tvg-logo", "")}" '
            f'group-title="{channel.get("group-title", "")}",{channel.get("name", "")}\n'
            f'{channel.get("url", "")}\n'
        )

    return Response(m3u, mimetype="audio/x-mpegurl")

@app.route("/epg.xml")
def epg():
    channels = get_channels()
    xml = generate_epg(channels)
    return Response(xml, mimetype="application/xml")

@app.route("/channels.json")
def channels_json():
    """Endpoint para visualizar os canais em JSON"""
    channels = load_channels()
    return Response(json.dumps(channels, indent=2, ensure_ascii=False), 
                    mimetype="application/json")

@app.route("/health")
def health():
    return {"status": "ok", "channels_count": len(get_channels())}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))