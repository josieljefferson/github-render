import requests
import gzip
import io
import json

# Carregar EPG sources do channels.json
def get_epg_sources():
    try:
        with open('channels.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('metadata', {}).get('epg_sources', [])
    except:
        # Fontes de EPG padrão como fallback
        return [
            "https://m3u4u.com/epg/jq2zy9epr3bwxmgwyxr5",
            "https://m3u4u.com/epg/3wk1y24kx7uzdevxygz7",
            "https://m3u4u.com/epg/782dyqdrqkh1xegen4zp",
            "https://www.open-epg.com/files/brazil1.xml.gz",
            "https://www.open-epg.com/files/brazil2.xml.gz",
            "https://www.open-epg.com/files/brazil3.xml.gz",
            "https://www.open-epg.com/files/brazil4.xml.gz",
            "https://www.open-epg.com/files/portugal1.xml.gz",
            "https://www.open-epg.com/files/portugal2.xml.gz",
            "https://epgshare01.online/epgshare01/epg_ripper_BR1.xml.gz",
            "https://epgshare01.online/epgshare01/epg_ripper_PT1.xml.gz"
        ]

def generate_epg(channels_dict):
    """
    Gera EPG XML a partir das fontes configuradas
    e filtra apenas os canais que temos na playlist
    """
    all_epg_data = []
    epg_sources = get_epg_sources()
    
    # Coletar dados de todas as fontes EPG
    for url in epg_sources:
        try:
            print(f"Baixando EPG de: {url}")
            
            if url.endswith('.gz'):
                # Processar arquivos GZIP
                r = requests.get(url, timeout=15)
                if r.status_code == 200:
                    data = gzip.GzipFile(fileobj=io.BytesIO(r.content)).read().decode("utf-8", errors='ignore')
                    all_epg_data.append(data)
            else:
                # Processar URLs XML normais
                r = requests.get(url, timeout=15)
                if r.status_code == 200:
                    all_epg_data.append(r.text)
        except Exception as e:
            print(f"Erro ao baixar EPG de {url}: {e}")
            continue
    
    # Se nenhum EPG foi baixado, retornar XML básico
    if not all_epg_data:
        return create_basic_epg(channels_dict)
    
    # Combinar todos os dados EPG e filtrar
    return combine_and_filter_epg(all_epg_data, channels_dict)

def combine_and_filter_epg(epg_data_list, channels_dict):
    """
    Combina múltiplos feeds EPG e filtra apenas os canais que temos
    """
    # Extrair IDs de canal para filtro
    channel_ids = {channel.get('tvg_id', '') for channel in channels_dict.values()}
    channel_names = {channel['name'].lower() for channel in channels_dict.values()}
    
    combined_epg = ['<?xml version="1.0" encoding="UTF-8"?>', '<tv>']
    
    for epg_data in epg_data_list:
        # Extrair apenas as tags <channel> e <programme> do EPG
        lines = epg_data.split('\n')
        in_tv_tag = False
        
        for line in lines:
            line_stripped = line.strip()
            
            if '<tv>' in line_stripped:
                in_tv_tag = True
                continue
            elif '</tv>' in line_stripped:
                in_tv_tag = False
                continue
            
            if in_tv_tag:
                # Filtrar canais pelo ID
                if '<channel id="' in line_stripped:
                    for channel_id in channel_ids:
                        if channel_id and f'id="{channel_id}"' in line_stripped:
                            combined_epg.append(line_stripped)
                            break
                # Filtrar programas pelo ID do canal
                elif '<programme' in line_stripped:
                    for channel_id in channel_ids:
                        if channel_id and f'channel="{channel_id}"' in line_stripped:
                            combined_epg.append(line_stripped)
                            break
    
    combined_epg.append('</tv>')
    return '\n'.join(combined_epg)

def create_basic_epg(channels_dict):
    """
    Cria um EPG básico quando não há fontes disponíveis
    """
    epg = ['<?xml version="1.0" encoding="UTF-8"?>', '<tv>']
    
    for channel_id, channel in channels_dict.items():
        # Adicionar entrada de canal
        epg.append(f'<channel id="{channel.get("tvg_id", channel_id)}">')
        epg.append(f'<display-name>{channel["name"]}</display-name>')
        if channel.get("logo"):
            epg.append(f'<icon src="{channel["logo"]}"/>')
        epg.append('</channel>')
        
        # Adicionar programa básico
        epg.append(f'<programme start="20250101000000 +0000" stop="20251231235959 +0000" channel="{channel.get("tvg_id", channel_id)}">')
        epg.append('<title>Programação Disponível</title>')
        epg.append('<desc>Assista a este canal via IPTV</desc>')
        epg.append('</programme>')
    
    epg.append('</tv>')
    return '\n'.join(epg)

def get_channels_from_json():
    """
    Função auxiliar para obter canais do JSON
    """
    try:
        with open('channels.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('channels', [])
    except:
        return []