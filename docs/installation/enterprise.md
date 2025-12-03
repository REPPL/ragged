# Enterprise Installation Guide

Deploy ragged in enterprise environments with silent installation, multi-user setup, and centralised management.

## Overview

Enterprise installations differ from personal installations:

| Feature | Personal | Enterprise |
|---------|----------|------------|
| Installation | Interactive | Silent/Automated |
| Users | Single | Multiple |
| Authentication | None | LDAP/AD/SSO |
| Storage | Local | Network (NFS/SMB) |
| Configuration | Per-user | Centralised |
| Monitoring | Basic | Full observability |

## Silent Installation

### Windows (PowerShell)

```powershell
# Download installer
Invoke-WebRequest -Uri "https://install.ragged.ai/windows/ragged-installer.exe" -OutFile "ragged-installer.exe"

# Run silent installation
.\ragged-installer.exe /S /CONFIG="C:\path\to\config.yaml"
```

### macOS/Linux (Bash)

```bash
# Silent installation with configuration
curl -sSL https://install.ragged.ai | sh -s -- \
    --silent \
    --config /path/to/config.yaml \
    --accept-license
```

### Configuration File for Silent Install

```yaml
# enterprise-config.yaml
installation:
  mode: enterprise
  accept_license: true
  skip_prompts: true

paths:
  home: /opt/ragged
  documents: /data/ragged/documents
  cache: /data/ragged/cache
  logs: /var/log/ragged

services:
  api_port: 8000
  webui_port: 5173
  bind_address: 0.0.0.0  # Allow external access

authentication:
  enabled: true
  provider: ldap  # or 'oidc', 'local'
  ldap:
    server: ldap://ldap.company.com:389
    base_dn: dc=company,dc=com
    bind_dn: cn=ragged,ou=services,dc=company,dc=com
    bind_password_env: RAGGED_LDAP_PASSWORD
    user_filter: "(uid={username})"
    group_filter: "(member={dn})"
    admin_group: cn=ragged-admins,ou=groups,dc=company,dc=com

storage:
  type: network  # or 'local'
  nfs:
    server: nfs.company.com
    export: /exports/ragged
    mount_point: /data/ragged
```

---

## Configuration Management

### Ansible Playbook

```yaml
# ragged.yml
---
- name: Install and configure ragged
  hosts: ragged_servers
  become: yes
  vars:
    ragged_version: "0.8.7"
    ragged_home: /opt/ragged
    ragged_data: /data/ragged

  tasks:
    - name: Install dependencies
      apt:
        name:
          - docker.io
          - docker-compose
          - python3
          - python3-pip
        state: present
        update_cache: yes

    - name: Add ragged user
      user:
        name: ragged
        system: yes
        home: "{{ ragged_home }}"
        shell: /bin/bash
        groups: docker

    - name: Install ragged
      pip:
        name: ragged
        version: "{{ ragged_version }}"
        executable: pip3

    - name: Create data directories
      file:
        path: "{{ item }}"
        state: directory
        owner: ragged
        group: ragged
        mode: '0750'
      loop:
        - "{{ ragged_data }}/documents"
        - "{{ ragged_data }}/cache"
        - "{{ ragged_data }}/logs"

    - name: Deploy configuration
      template:
        src: ragged-config.yaml.j2
        dest: "{{ ragged_home }}/config.yaml"
        owner: ragged
        group: ragged
        mode: '0600'
      notify: Restart ragged

    - name: Install systemd service
      template:
        src: ragged.service.j2
        dest: /etc/systemd/system/ragged.service
      notify:
        - Reload systemd
        - Restart ragged

    - name: Enable and start ragged
      systemd:
        name: ragged
        enabled: yes
        state: started

  handlers:
    - name: Reload systemd
      systemd:
        daemon_reload: yes

    - name: Restart ragged
      systemd:
        name: ragged
        state: restarted
```

### Puppet Manifest

```puppet
# ragged.pp
class ragged (
  String $version = '0.8.7',
  String $home = '/opt/ragged',
  String $data = '/data/ragged',
) {
  package { ['docker.io', 'python3', 'python3-pip']:
    ensure => installed,
  }

  user { 'ragged':
    ensure     => present,
    system     => true,
    home       => $home,
    managehome => true,
    groups     => ['docker'],
    require    => Package['docker.io'],
  }

  exec { 'install-ragged':
    command => "/usr/bin/pip3 install ragged==${version}",
    unless  => "/usr/bin/pip3 show ragged | grep -q ${version}",
    require => Package['python3-pip'],
  }

  file { [$data, "${data}/documents", "${data}/cache", "${data}/logs"]:
    ensure => directory,
    owner  => 'ragged',
    group  => 'ragged',
    mode   => '0750',
  }

  file { "${home}/config.yaml":
    ensure  => file,
    content => template('ragged/config.yaml.erb'),
    owner   => 'ragged',
    group   => 'ragged',
    mode    => '0600',
    notify  => Service['ragged'],
  }

  file { '/etc/systemd/system/ragged.service':
    ensure  => file,
    content => template('ragged/ragged.service.erb'),
    notify  => Exec['systemd-reload'],
  }

  exec { 'systemd-reload':
    command     => '/bin/systemctl daemon-reload',
    refreshonly => true,
  }

  service { 'ragged':
    ensure  => running,
    enable  => true,
    require => [File['/etc/systemd/system/ragged.service'], Exec['install-ragged']],
  }
}
```

---

## Multi-User Setup

### User Isolation

Each user gets their own document space:

```yaml
# config.yaml
multiuser:
  enabled: true
  isolation: full  # or 'shared'
  user_directory: /data/ragged/users/{username}
  shared_directory: /data/ragged/shared
```

### Permission Model

```yaml
permissions:
  default_role: user
  roles:
    admin:
      - documents:*
      - settings:*
      - users:*
    user:
      - documents:own
      - documents:shared:read
      - settings:own
    viewer:
      - documents:shared:read
```

### User Provisioning

```bash
# Create user
ragged user create --username jsmith --role user

# Assign to group
ragged group add-user --group engineering --username jsmith

# Grant document access
ragged permissions grant --user jsmith --resource /shared/docs --action read
```

---

## LDAP/Active Directory Integration

### LDAP Configuration

```yaml
authentication:
  provider: ldap
  ldap:
    # Connection
    server: ldap://ldap.company.com:389
    use_ssl: true
    ssl_cert_verify: true
    timeout: 10

    # Binding
    bind_dn: cn=ragged,ou=services,dc=company,dc=com
    bind_password_env: RAGGED_LDAP_PASSWORD

    # User search
    base_dn: dc=company,dc=com
    user_filter: "(&(objectClass=user)(sAMAccountName={username}))"
    user_attr_map:
      username: sAMAccountName
      email: mail
      display_name: displayName

    # Group mapping
    group_base_dn: ou=groups,dc=company,dc=com
    group_filter: "(member={dn})"
    admin_groups:
      - cn=ragged-admins,ou=groups,dc=company,dc=com
    user_groups:
      - cn=ragged-users,ou=groups,dc=company,dc=com
```

### Active Directory Configuration

```yaml
authentication:
  provider: ldap
  ldap:
    server: ldap://ad.company.com:389
    use_ssl: true

    # AD-specific settings
    bind_dn: ragged@company.com
    bind_password_env: RAGGED_AD_PASSWORD

    base_dn: dc=company,dc=com
    user_filter: "(&(objectCategory=person)(objectClass=user)(sAMAccountName={username}))"

    # Nested group support
    group_filter: "(member:1.2.840.113556.1.4.1941:={dn})"
```

---

## Network Storage

### NFS Configuration

```yaml
storage:
  type: nfs
  nfs:
    server: nfs.company.com
    export: /exports/ragged
    mount_point: /data/ragged
    options: "rw,sync,hard,intr"
```

Mount command:
```bash
sudo mount -t nfs -o rw,sync,hard,intr nfs.company.com:/exports/ragged /data/ragged
```

Add to `/etc/fstab`:
```
nfs.company.com:/exports/ragged /data/ragged nfs rw,sync,hard,intr 0 0
```

### SMB/CIFS Configuration

```yaml
storage:
  type: smb
  smb:
    server: //fileserver.company.com/ragged
    mount_point: /data/ragged
    username_env: RAGGED_SMB_USER
    password_env: RAGGED_SMB_PASSWORD
    domain: COMPANY
```

Mount command:
```bash
sudo mount -t cifs //fileserver.company.com/ragged /data/ragged \
    -o username=$RAGGED_SMB_USER,password=$RAGGED_SMB_PASSWORD,domain=COMPANY
```

---

## High Availability

### Architecture

```
                    ┌─────────────────┐
                    │   Load Balancer │
                    │   (HAProxy/NGINX)│
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
     ┌────────────┐   ┌────────────┐   ┌────────────┐
     │  Ragged 1  │   │  Ragged 2  │   │  Ragged 3  │
     └──────┬─────┘   └──────┬─────┘   └──────┬─────┘
            │                │                │
            └────────────────┼────────────────┘
                             ▼
                    ┌─────────────────┐
                    │  Shared Storage │
                    │   (NFS/S3)      │
                    └─────────────────┘
```

### HAProxy Configuration

```haproxy
frontend ragged_frontend
    bind *:8000
    default_backend ragged_backend

backend ragged_backend
    balance roundrobin
    option httpchk GET /health
    server ragged1 192.168.1.10:8000 check
    server ragged2 192.168.1.11:8000 check
    server ragged3 192.168.1.12:8000 check
```

### Session Persistence

```yaml
# config.yaml
session:
  type: redis  # or 'database'
  redis:
    host: redis.company.com
    port: 6379
    password_env: RAGGED_REDIS_PASSWORD
    db: 0
```

---

## Monitoring and Observability

### Prometheus Metrics

```yaml
monitoring:
  prometheus:
    enabled: true
    port: 9090
    path: /metrics
```

### Grafana Dashboard

Import the ragged dashboard from:
```
https://grafana.com/grafana/dashboards/ragged
```

### Log Aggregation

```yaml
logging:
  format: json
  level: INFO
  outputs:
    - type: file
      path: /var/log/ragged/ragged.log
    - type: syslog
      server: syslog.company.com:514
    - type: elasticsearch
      hosts:
        - https://es.company.com:9200
      index: ragged-logs
```

---

## Security Hardening

See [Installation Security](../guides/security/) for comprehensive security configuration.

Key enterprise security settings:

```yaml
security:
  # TLS/HTTPS
  tls:
    enabled: true
    cert_file: /etc/ragged/tls/cert.pem
    key_file: /etc/ragged/tls/key.pem

  # API Security
  api:
    rate_limit: 100  # requests per minute
    max_request_size: 100MB
    allowed_origins:
      - https://ragged.company.com

  # Audit logging
  audit:
    enabled: true
    log_file: /var/log/ragged/audit.log
```

---

## Related Documentation

- [Security Reference](../guides/security/)
- [API Reference](../reference/api/)
- [Troubleshooting](../troubleshooting/README.md)
- [Offline Installation](./offline.md)

---
