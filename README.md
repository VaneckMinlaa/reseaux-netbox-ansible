# Standardisation des configs réseau

Pipeline : **NetBox (SoT) → Jinja2 → validation → déploiement progressif → détection de dérive**.

Fonctionne en mode **demo** (YAML local) sans NetBox, puis bascule sur NetBox réel. **Sans Docker.**

## Architecture

```
NetBox / data/demo_devices.yaml
        │
        ▼
 scripts/cli.py generate   →  configs/expected/*.cfg   (Jinja2)
        │
        ▼
 scripts/cli.py validate   →  règles métier (CI)
        │
        ▼
 playbooks/deploy.yml      →  site pilote puis prod (Ansible, manuel)
        │
        ▼
 playbooks/drift.yml       →  collecte running + scripts/cli.py drift (nightly)
```

## Prérequis

| Outil | Où |
|-------|-----|
| Python 3.11+ | PC Windows ou VM Ubuntu |
| Ansible + collections | VM Ubuntu recommandée (déploiement SSH) |
| NetBox | Install from source sur Ubuntu (**pas Docker**) — voir `docs/setup-sans-docker.md` |
| PNETLab | Switches lab |
| GitLab | gitlab.com ou instance self-hosted |

## Démarrage rapide (Windows — mode demo)

```powershell
cd "D:\Projects\Projet GitHub\DevOps\Reseaux"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env

python scripts\cli.py generate
python scripts\cli.py validate
```

Introduire une dérive simulée puis la détecter :

```powershell
copy configs\expected\*.cfg configs\running\
Add-Content configs\running\SW-PROD-01.cfg "`ninterface Loopback99`n description DRIFT-TEST`n"
python scripts\cli.py drift
```

Le rapport est écrit dans `reports/`.

## Sites & inventaire demo

| Host | Site | Platform | IP lab (à adapter) |
|------|------|----------|--------------------|
| SW-PILOTE-01 | pilote | cisco_ios | 10.10.10.11 |
| SW-PILOTE-02 | pilote | arista_eos | 10.10.10.12 |
| SW-PROD-01 | prod-sim | cisco_ios | 10.20.20.11 |

Filtrer un site :

```powershell
python scripts\cli.py generate --site pilote
python scripts\cli.py validate --site pilote
```

## Ansible (sur VM Ubuntu avec accès SSH aux switches)

```bash
pip install -r requirements.txt
pip install ansible
ansible-galaxy collection install -r requirements-ansible.yml

ansible-playbook playbooks/generate.yml
ansible-playbook playbooks/validate.yml
ansible-playbook playbooks/deploy.yml -i inventories/demo/hosts.yml --limit site_pilote
ansible-playbook playbooks/drift.yml  -i inventories/demo/hosts.yml
```

Inventaire NetBox dynamique :

```bash
export NETBOX_URL=http://192.168.x.x:8000
export NETBOX_TOKEN=...
export SOURCE_MODE=netbox
ansible-inventory -i inventories/netbox.yml --list
```

## GitLab CI

Fichier `.gitlab-ci.yml` :

1. **generate** / **validate** — automatiques  
2. **deploy_pilot** — manuel  
3. **deploy_prod** — manuel après pilote  
4. **drift** — schedule nightly (`0 2 * * *`) avec variable `DRIFT_FAIL=1`

Variables CI à définir : `NETBOX_URL`, `NETBOX_TOKEN`, `SOURCE_MODE`, `ANSIBLE_NETWORK_USER`, `ANSIBLE_NETWORK_PASSWORD`.

## Documentation

- `docs/setup-sans-docker.md` — NetBox + Ansible sur Ubuntu sans Docker  
- `docs/netbox-model.md` — modèle de données NetBox  
- `docs/lab-pnetlab.md` — topo PNETLab recommandée  
- `docs/runbook.md` — runbook ops quotidien  

## Structure

```
netops/                 # moteur Python (source, render, validate, drift)
scripts/cli.py          # CLI
templates/              # Jinja2 multi-vendor
data/demo_devices.yaml  # SoT offline
playbooks/              # generate, validate, deploy, drift
inventories/            # demo YAML + plugin NetBox
configs/expected|running/
reports/
```
