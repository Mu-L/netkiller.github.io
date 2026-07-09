#!/usr/bin/env python3

from __future__ import annotations

import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://www.netkiller.cn"
SCRIPT_ID = "netkiller-jsonld"
SCRIPT_RE = re.compile(
    rf'<script\s+type="application/ld\+json"\s+id="{SCRIPT_ID}">.*?</script>',
    re.DOTALL,
)

AUTHOR = {
    "@type": "Person",
    "@id": f"{BASE_URL}/home/about.html#neo-chan",
    "name": "Neo Chan",
    "alternateName": "陈景峰",
    "email": "netkiller@msn.com",
    "url": f"{BASE_URL}/home/about.html",
    "sameAs": [
        "https://github.com/netkiller",
        "https://zhuanlan.zhihu.com/netkiller",
        "https://blog.csdn.net/u010604770",
        "https://my.oschina.net/neochen/",
    ],
}

CORE_BOOKS = {
    "management/index.html": ("Netkiller Management 手札", "Management, business, product, marketing, operations management, and digital transformation notes."),
    "architect/index.html": ("Netkiller Architect 手札", "Architecture, system design, distributed systems, database architecture, operations architecture, and high-availability design."),
    "linux/index.html": ("Netkiller Linux 手札", "Linux administration, system services, shell usage, kernel and operations practices."),
    "android/index.html": ("Netkiller Android 手札", "Android application development, activities, services, broadcast receivers, storage, media, resources, and device APIs."),
    "java/index.html": ("Netkiller Java 手札", "Java language, JVM ecosystem, Java frameworks, middleware, Android-related Java notes, and application development."),
    "spring/index.html": ("Netkiller Spring 手札", "Spring Framework, Spring Boot, Spring Cloud, Spring Security, data access, messaging, and service development."),
    "python/index.html": ("Netkiller Python 手札", "Python development, scripting, frameworks, and operations-related Python usage."),
    "docbook/index.html": ("Netkiller DocBook 手札", "DocBook authoring and documentation generation notes."),
    "devops/index.html": ("Netkiller DevOps 手札", "DevOps, automation, deployment, CI/CD, monitoring, and operations workflows."),
    "container/index.html": ("Netkiller Container 手札", "Containers, Docker, Kubernetes, registries, orchestration, and cloud-native infrastructure."),
    "monitor/index.html": ("Netkiller Monitor 手札", "Monitoring and observability notes."),
    "www/index.html": ("Netkiller Web 手札", "Web servers and application servers including Nginx, Apache, Tomcat, Varnish, Resin, Traffic Server, and web operations."),
    "database/index.html": ("Netkiller Database 手札", "General database notes, database design, SQL, backup, replication, and operations topics."),
    "mysql/index.html": ("Netkiller MySQL 手札", "MySQL administration, SQL examples, replication, clustering, performance, and troubleshooting."),
    "postgresql/index.html": ("Netkiller PostgreSQL 手札", "PostgreSQL usage, operations, SQL, extensions, backup, replication, and administration."),
    "nosql/index.html": ("Netkiller NoSQL 手札", "NoSQL systems including MongoDB, Redis, Cassandra, and related database platforms."),
    "shell/index.html": ("Netkiller Shell 手札", "Shell scripting, Unix command-line usage, automation, and operational scripts."),
    "blockchain/index.html": ("Netkiller Blockchain 手札", "Blockchain-related technical notes."),
    "security/index.html": ("Netkiller Security 手札", "Security operations, hardening, VPN, cryptography, firewall, authentication, and infrastructure security topics."),
    "network/index.html": ("Netkiller Network 手札", "Networking, routing, switching, TCP/IP, firewalling, and network infrastructure notes."),
}


def website_graph() -> dict:
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": f"{BASE_URL}/#website",
                "name": "Netkiller 系列免费电子书",
                "alternateName": "Netkiller Series Free Ebooks",
                "url": f"{BASE_URL}/",
                "inLanguage": "zh-CN",
                "description": "Netkiller is a long-running collection of free technical ebooks and notes covering Linux, databases, DevOps, networking, security, programming languages, Java/Spring, Android, architecture, and IT operations topics.",
                "publisher": {"@id": AUTHOR["@id"]},
                "author": {"@id": AUTHOR["@id"]},
            },
            AUTHOR,
        ],
    }


def book_graph(path: str, name: str, description: str) -> dict:
    url = f"{BASE_URL}/{path}"
    return {
        "@context": "https://schema.org",
        "@type": "Book",
        "@id": f"{url}#book",
        "name": name,
        "url": url,
        "inLanguage": "zh-CN",
        "isAccessibleForFree": True,
        "bookFormat": "https://schema.org/EBook",
        "description": description,
        "author": AUTHOR,
        "publisher": AUTHOR,
        "isPartOf": {
            "@type": "CreativeWorkSeries",
            "@id": f"{BASE_URL}/#series",
            "name": "Netkiller 系列手札",
            "url": f"{BASE_URL}/",
        },
    }


def inject(path: Path, data: dict) -> bool:
    original = path.read_text(encoding="utf-8")
    script = (
        f'<script type="application/ld+json" id="{SCRIPT_ID}">\n'
        f'{json.dumps(data, ensure_ascii=False, indent=2)}\n'
        "</script>"
    )
    text = SCRIPT_RE.sub("", original)
    if "</head>" not in text:
        raise ValueError(f"{path} does not contain </head>")
    updated = text.replace("</head>", f"{script}</head>", 1)
    if updated == original:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def main() -> None:
    updated = 0
    if inject(REPO_ROOT / "index.html", website_graph()):
        updated += 1

    for rel_path, (name, description) in CORE_BOOKS.items():
        path = REPO_ROOT / rel_path
        if path.exists() and inject(path, book_graph(rel_path, name, description)):
            updated += 1

    print(f"Updated JSON-LD in {updated} files")


if __name__ == "__main__":
    main()
