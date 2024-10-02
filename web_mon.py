from pyzabbix import ZabbixAPI
import re

zabbix_server = 'http://192.168.58.151/zabbix'
zabbix_username = 'Admin'
zabbix_password = 'zabbix'

try:
    zapi = ZabbixAPI(zabbix_server)
    zapi.login(zabbix_username, zabbix_password)
    print("Autenticado no Zabbix com sucesso!")
except Exception as e:
    print(f"Erro ao conectar ao Zabbix: {e}")
    exit()


def validate_url(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// ou https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domínio
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ou IP
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ou IPv6
        r'(?::\d+)?'  # porta opcional
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    return re.match(regex, url) is not None


def create_host(hostname, group_id):
    try:
        host = zapi.host.create({
            "host": hostname,
            "groups": [{"groupid": group_id}],
        })
        return host['hostids'][0]
    except Exception as e:
        print(f"Erro ao criar host: {e}")
        return None


def web_create(url, hostid):
    if not validate_url(url):
        print("URL inválida!")
        return
    try:
        #interval (5 min ou 300 seg)
        response = zapi.httptest.create({
            "name": "Monitoração URL",
            "hostid": hostid,
            "retries": "3",
            "agent": "Chrome 80 (Linux)",
            "delay": "5m",
            "steps": [
                {
                    "name": url,
                    "url": url,
                    "status_codes": "200-499",
                    "no": 1
                }
            ]
        })
        httptest_id = response['httptestids'][0]
        print(f"Teste de URL criado com sucesso! ID do teste: {httptest_id}")

        trigger_create = zapi.trigger.create({
            "description": f"Alerta: Status HTTP > 499 para {url}",
            "expression": f"{{{hostid}.web.test.rspcode[{httptest_id},1].last}} > 499",
            "priority": 5,
            "status": 0
        })

        print(f"Trigger criado com sucesso! ID do trigger: {trigger_create['triggerids'][0]}")
    except Exception as er:
        print(f"Erro ao criar o teste HTTP ou trigger: {er}")


if __name__ == "__main__":
    opt = input("Deseja criar um host:\n[1] Sim\n[2] Não\n>>>")

    if opt == '1':
        hostname = input("Digite o Hostname: ")
        group_id = input("Digite o group_id: ")
        hostid = create_host(hostname, group_id)
        if hostid:
            print(f"HostID criado - {hostid}")
            url = input("Por favor, insira a URL que deseja monitorar: ")
            web_create(url, hostid)
        else:
            print("Falha ao criar o host.")
            exit()
    if opt == '2':
        hostid = input("Digite o HostID existente: ")
        url = input("Por favor, insira a URL que deseja monitorar: ")
        web_create(url, hostid)
    else:
        print("Selecione uma opção válida [1] ou [2]")
        exit()


