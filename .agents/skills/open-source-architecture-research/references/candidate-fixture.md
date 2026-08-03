# Candidate metadata format / 候选项目元数据格式

Use this JSON shape when a host GitHub or web-search tool collects public candidates after API rate
limiting. Keep original source URLs and do not add unverified values.

```json
[
  {
    "full_name": "owner/repository",
    "html_url": "https://github.com/owner/repository",
    "description": "public repository summary",
    "topics": ["public-topic"],
    "stargazers_count": 1000,
    "updated_at": "2026-08-03T00:00:00Z",
    "archived": false,
    "private": false,
    "license": {"spdx_id": "Apache-2.0"}
  }
]
```

`full_name`, `html_url`, `stargazers_count`, `updated_at`, `archived`, `private`, and `license` are
required evidence for an eligible high-star reference. Omit a field only when it is truly
unavailable; the ranker will block that candidate and the final recommendation must record the
missing evidence as an open decision instead of treating it as confirmed.
