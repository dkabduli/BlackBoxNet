# BlackBoxNet - Technology Stack
## Dependencies and Versions

**Version:** 1.0  
**Date:** 2024-11-15

---

## Backend Stack

### Core Framework

**FastAPI 0.104+**
- Modern Python web framework
- Async/await support
- Automatic OpenAPI documentation
- Type hints with Pydantic
- High performance (Starlette + uvicorn)

**Why FastAPI:**
- Best-in-class API documentation
- Native async support for database operations
- Excellent type safety
- Growing ecosystem

---

### Database

**PostgreSQL 15+**
- Primary database
- JSONB support for flexible metadata
- Array types for tags
- Strong ACID guarantees
- Excellent performance

**Why PostgreSQL:**
- JSONB for metadata without schema changes
- Native INET type for IP addresses
- Robust transaction support
- Battle-tested for time-series data

**SQLAlchemy 2.0+**
- ORM for database access
- Async support
- Type-safe queries
- Migration support via Alembic

**Alembic 1.12+**
- Database migration tool
- Version control for schema
- Rollback support

---

### Git Integration

**GitPython 3.1+**
- Pure Python Git implementation
- Simple API
- No external dependencies beyond Git binary
- Good documentation

**Why GitPython:**
- Easy to use
- No C bindings (unlike pygit2)
- Sufficient for Phase 1 needs

---

### Python Dependencies

**Core:**
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9  # PostgreSQL adapter
gitpython==3.1.40
pydantic==2.5.0
python-dateutil==2.8.2
```

**Development:**
```
pytest==7.4.3
pytest-cov==4.1.0
pytest-asyncio==0.21.1
httpx==0.25.2  # For testing FastAPI
```

**Utilities:**
```
python-dotenv==1.0.0  # Environment variables
```

---

## Frontend Stack

### Core Framework

**React 18.2+**
- Component-based UI
- Hooks for state management
- Large ecosystem
- Excellent documentation

**TypeScript 5.3+**
- Type safety
- Better IDE support
- Catches errors at compile time

**Why React + TypeScript:**
- Industry standard
- Excellent tooling
- Type safety prevents runtime errors

---

### Build Tool

**Vite 5.0+**
- Fast HMR (Hot Module Replacement)
- Modern ES modules
- Better DX than Create React App
- Optimized production builds

**Why Vite:**
- 10-100x faster than webpack in dev mode
- Simple configuration
- Great TypeScript support

---

### UI Framework

**shadcn/ui + Tailwind CSS 3.3+**
- Copy-paste components (no runtime overhead)
- Fully customizable
- Accessible (built on Radix UI)
- Utility-first CSS with Tailwind

**Why shadcn/ui:**
- No package bloat (components copied to your project)
- Full control over styling
- Excellent accessibility
- Modern design

**Alternatives considered:**
- Material-UI: Too heavy, harder to customize
- Ant Design: Less modern aesthetic
- Chakra UI: Runtime CSS-in-JS overhead

---

### Frontend Dependencies

**Core:**
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.2",
    "date-fns": "^2.30.0"
  }
}
```

**UI & Visualization:**
```json
{
  "dependencies": {
    "@radix-ui/react-*": "^1.0.0",
    "react-diff-view": "^3.2.1",
    "react-syntax-highlighter": "^15.5.0",
    "lucide-react": "^0.294.0"
  }
}
```

**Development:**
```json
{
  "devDependencies": {
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@vitejs/plugin-react": "^4.2.1",
    "typescript": "^5.3.3",
    "vite": "^5.0.8",
    "tailwindcss": "^3.3.6",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32",
    "eslint": "^8.55.0",
    "prettier": "^3.1.1"
  }
}
```

---

## Infrastructure

### Containerization

**Docker 24+**
- Container runtime
- Consistent environments
- Easy deployment

**Docker Compose 2.0+**
- Multi-container orchestration
- Development environment
- Service dependencies

**Why Docker:**
- Eliminates "works on my machine"
- Easy to add new services
- Production-like local development

---

### Reverse Proxy

**Nginx (in Docker)**
- Serve frontend static files
- Proxy API requests
- Single entry point

**Why Nginx:**
- Industry standard
- High performance
- Simple configuration for Phase 1

---

## Version Control

**Git 2.40+**
- Source control for code
- Configuration versioning (in app)

**GitHub/GitLab**
- Remote repository hosting
- CI/CD integration (future)

---

## Development Tools

### Code Editor

**Cursor (VS Code fork)**
- AI-powered coding
- GitHub Copilot integration
- Excellent TypeScript support

**VS Code (alternative)**
- Free and open source
- Rich extension ecosystem

---

### Python Tools

**Black**
- Code formatter
- Consistent style

**Ruff**
- Fast Python linter
- Replaces flake8, isort, etc.

**mypy**
- Static type checker
- Catches type errors

---

### JavaScript/TypeScript Tools

**ESLint**
- JavaScript linter
- Catches common errors

**Prettier**
- Code formatter
- Consistent style

---

## Testing Tools

### Backend Testing

**pytest**
- Python testing framework
- Rich plugin ecosystem
- Fixtures for setup/teardown

**pytest-cov**
- Code coverage reporting
- Integrates with pytest

**pytest-asyncio**
- Async test support
- Required for SQLAlchemy async tests

**httpx**
- HTTP client for testing FastAPI
- Async support

---

### Frontend Testing (Optional Phase 1)

**Vitest**
- Unit testing for Vite projects
- Fast, Jest-compatible API

**React Testing Library**
- Component testing
- User-centric tests

**Playwright (future)**
- E2E testing
- Multi-browser support

---

## Deployment Stack (Future)

### Phase 2+

**Kubernetes**
- Container orchestration
- Scaling
- Self-healing

**Helm**
- Kubernetes package manager
- Templated deployments

**PostgreSQL HA**
- Patroni or similar
- High availability
- Automatic failover

---

## Monitoring & Observability (Future)

### Phase 2+

**Prometheus**
- Metrics collection
- Time-series database

**Grafana**
- Metrics visualization
- Dashboards

**Sentry**
- Error tracking
- Performance monitoring

**Structured Logging**
- python-json-logger
- Centralized log aggregation

---

## Why These Choices?

### Python Ecosystem

**Pros:**
- FastAPI is modern, fast, and has excellent docs
- SQLAlchemy 2.0 has native async support
- Strong typing with Pydantic
- Great testing tools

**Cons:**
- Async can be complex for beginners
- Migration: Python ecosystem fragmentation

**Alternatives Considered:**
- Flask: Too basic, no async support
- Django: Too heavy for API-only service
- Node.js: Less type-safe, callback hell

---

### React Ecosystem

**Pros:**
- Industry standard, huge ecosystem
- TypeScript support excellent
- shadcn/ui is modern and customizable
- Vite is blazing fast

**Cons:**
- Boilerplate can be verbose
- Many ways to do the same thing

**Alternatives Considered:**
- Vue: Smaller ecosystem
- Svelte: Too new, smaller community
- Angular: Too heavy, steep learning curve

---

### PostgreSQL

**Pros:**
- Best open-source RDBMS
- JSONB for flexibility
- Excellent performance
- Great community

**Cons:**
- More complex than SQLite
- Requires separate service

**Alternatives Considered:**
- MySQL: Weaker JSON support
- MongoDB: Wrong fit for relational data
- SQLite: Not production-ready

---

## Dependency Management

### Backend

**requirements.txt**
- Simple, widely supported
- pip install -r requirements.txt

**pyproject.toml** (future)
- Modern Python standard
- Poetry or PDM for dependency resolution

---

### Frontend

**package-lock.json**
- Ensures reproducible builds
- npm ci for CI/CD

---

## Version Pinning Strategy

### Backend

**Exact versions** for production dependencies:
```
fastapi==0.104.1  # Not ^0.104.1
```

**Why:** Reproducible builds, avoid breaking changes

---

### Frontend

**Caret ranges** for most dependencies:
```json
"react": "^18.2.0"  // Allows 18.2.x, 18.3.x, not 19.x
```

**Why:** Get security patches, avoid major breaking changes

---

## Security Considerations

### Known Vulnerabilities

- Keep dependencies updated
- Run `npm audit` and `pip audit` regularly
- Use Dependabot or Renovate for automated updates

### Phase 1 Security Stance

**Local development only:**
- No authentication
- No HTTPS
- No input sanitization beyond Pydantic

**Phase 2+ Requirements:**
- JWT authentication
- HTTPS/TLS
- Input sanitization
- Rate limiting
- SQL injection prevention (parameterized queries)
- XSS prevention (React does this by default)

---

## Performance Targets

### Backend

- API response time: <500ms for timeline queries
- Database queries: <100ms for device health
- Config diff generation: <200ms

### Frontend

- Initial page load: <2s
- Route navigation: <500ms
- Timeline render: <1s for 100 events

### Database

- Snapshot inserts: <50ms
- Event queries: <100ms for incident timeline
- Full-text config search (future): <500ms

---

## Compatibility Matrix

### Backend

| Component       | Minimum Version | Tested Version |
|-----------------|-----------------|----------------|
| Python          | 3.11            | 3.11.6         |
| PostgreSQL      | 15              | 15.5           |
| Docker          | 24              | 24.0.7         |
| Docker Compose  | 2.0             | 2.23.3         |

### Frontend

| Component | Minimum Version | Tested Version |
|-----------|-----------------|----------------|
| Node.js   | 18              | 18.18.0        |
| npm       | 9               | 9.8.1          |

### Operating Systems

| OS         | Supported | Notes                          |
|------------|-----------|--------------------------------|
| macOS      | ✅         | Intel and Apple Silicon        |
| Linux      | ✅         | Ubuntu 22.04+, Debian 11+      |
| Windows    | ✅         | Via Docker Desktop WSL 2       |

---

## Resource Requirements

### Development

**Minimum:**
- CPU: 2 cores
- RAM: 8 GB
- Disk: 10 GB

**Recommended:**
- CPU: 4 cores
- RAM: 16 GB
- Disk: 20 GB

### Production (Phase 2+)

**Small deployment (10 devices):**
- CPU: 4 cores
- RAM: 8 GB
- Disk: 50 GB (SSD)

**Medium deployment (100 devices):**
- CPU: 8 cores
- RAM: 16 GB
- Disk: 200 GB (SSD)

---

## License Compliance

All dependencies use permissive licenses compatible with commercial use:

- FastAPI: MIT
- React: MIT
- PostgreSQL: PostgreSQL License (like BSD)
- Tailwind CSS: MIT
- shadcn/ui: MIT
- GitPython: BSD

**No GPL or AGPL dependencies** - safe for commercial use.

---

**END OF TECH STACK DOCUMENT**
