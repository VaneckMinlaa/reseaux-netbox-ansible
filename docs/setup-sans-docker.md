# Install sans Docker

Objectif : NetBox + Ansible + Python sur **Ubuntu Server** (VM VirtualBox / VMware à côté de PNETLab), sans conteneurs.

## 1. VM Ubuntu

- 2 vCPU, 4 Go RAM, 40 Go disque  
- Bridged ou même réseau virtuel que PNETLab  
- IP fixe (ex. `192.168.100.50`)

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv python3-dev \
  build-essential libxml2-dev libxslt1-dev libffi-dev libpq-dev \
  redis-server postgresql postgresql-contrib nginx git ansible
```

## 2. PostgreSQL

```bash
sudo -u postgres psql <<'SQL'
CREATE DATABASE netbox;
CREATE USER netbox WITH PASSWORD 'CHANGE_ME_DB';
ALTER DATABASE netbox OWNER TO netbox;
\c netbox
GRANT CREATE ON SCHEMA public TO netbox;
SQL
```

## 3. Redis

```bash
sudo systemctl enable redis-server --now
redis-cli ping   # PONG
```

## 4. NetBox from source

Suivre la doc officielle *Installation* (version figée recommandée) :

https://netboxlabs.com/docs/netbox/en/stable/installation/

Résumé :

```bash
sudo mkdir -p /opt/netbox && cd /opt/netbox
sudo git clone -b v4.2.4 --depth 1 https://github.com/netbox-community/netbox.git .
sudo python3 -m venv /opt/netbox/venv
source /opt/netbox/venv/bin/activate
pip install -U pip wheel
pip install -r /opt/netbox/netbox/requirements.txt
```

Configurer `/opt/netbox/netbox/netbox/configuration.py` :

- `ALLOWED_HOSTS = ['*']` (lab) ou hostname  
- `DATABASE` → user/password netbox  
- `REDIS` → localhost  
- `SECRET_KEY` → généré

Puis :

```bash
cd /opt/netbox/netbox
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --no-input
```

Créer les services systemd `netbox` + `netbox-rq` et un vhost nginx sur le port 80/8000 (voir doc officielle « Gunicorn / systemd / nginx »).

Créer un **API token** : NetBox UI → Profile → API Tokens.

## 5. Ce dépôt sur la VM

```bash
git clone <ton-repo> ~/Reseaux
cd ~/Reseaux
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install ansible
ansible-galaxy collection install -r requirements-ansible.yml
cp .env.example .env
# Éditer .env : SOURCE_MODE=netbox, NETBOX_URL, NETBOX_TOKEN, comptes SSH
```

## 6. Peupler NetBox

Voir `docs/netbox-model.md`. Créer sites `pilote` / `prod-sim`, platforms, devices, VLANs, interfaces, primary IP.

## 7. Vérifications

```bash
curl -H "Authorization: Token $NETBOX_TOKEN" $NETBOX_URL/api/dcim/devices/
python scripts/cli.py generate
python scripts/cli.py validate
ansible all -i inventories/demo/hosts.yml -m ping   # ou network_cli facts
```

## Note Windows / WSL

Si WSL2 est bloqué (`HCS_E_HYPERV_NOT_INSTALLED`) et que PNETLab utilise VMware/VirtualBox, **préfère cette VM Ubuntu** plutôt que d’activer Hyper-V (conflit fréquent avec les hyperviseurs type 2).
