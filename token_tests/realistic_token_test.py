#!/usr/bin/env python3
"""
Realistic Token Usage Comparison

This compares what an AI agent actually receives in context:
1. Traditional: Full project files + completed work history + notes
2. MCP: Only current rolling work plan (incomplete items only)

This should demonstrate the real token savings.
"""

import json
import tempfile
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_database, get_connection, create_work_item, complete_item, get_work_items_for_project, get_all_work_items_for_project, build_hierarchy, add_completion_summaries
from project_id import get_project_id

def estimate_tokens(text):
    """Simple token estimation (~4 chars per token)"""
    return len(text) // 4

def create_realistic_traditional_context():
    """
    What an AI agent typically gets with traditional file-based task management:
    - Main project file with ALL items (completed and incomplete)
    - Historical context files
    - Status files
    - Notes and documentation
    """
    
    main_project_file = """# E-Commerce Platform Development Project

## Project Overview
Building a full-stack e-commerce platform with React frontend, Node.js backend, and PostgreSQL database.
Started: January 2024 | Current Status: 65% Complete | Target: March 2024

## Phase 1: Backend Development [COMPLETED] ✅
### Task 1.1: Database Design [COMPLETED] ✅
- [x] Entity-relationship diagram (completed 2024-01-15)
- [x] Database schema design (completed 2024-01-16)
- [x] Create PostgreSQL database (completed 2024-01-18)
- [x] Set up connection pooling (completed 2024-01-19)
- [x] Database migrations framework (completed 2024-01-20)
- [x] Seed data scripts (completed 2024-01-22)
- [x] Database indexing strategy (completed 2024-01-24)
- [x] Backup and recovery procedures (completed 2024-01-25)

### Task 1.2: Authentication System [COMPLETED] ✅
- [x] JWT token implementation (completed 2024-01-26)
- [x] User registration endpoint (completed 2024-01-28)
- [x] User login endpoint (completed 2024-01-29) 
- [x] Password reset functionality (completed 2024-01-30)
- [x] Email verification system (completed 2024-02-01)
- [x] Role-based access control (completed 2024-02-02)
- [x] Session management (completed 2024-02-03)
- [x] OAuth2 integration (Google, Facebook) (completed 2024-02-05)

### Task 1.3: Product Management API [COMPLETED] ✅
- [x] Product CRUD endpoints (completed 2024-02-06)
- [x] Category management (completed 2024-02-07)
- [x] Image upload and storage (completed 2024-02-08)
- [x] Product search functionality (completed 2024-02-10)
- [x] Inventory tracking system (completed 2024-02-11)
- [x] Product pricing and discounts (completed 2024-02-12)
- [x] Product reviews and ratings (completed 2024-02-13)
- [x] Related products algorithm (completed 2024-02-14)

### Task 1.4: Order Management System [COMPLETED] ✅
- [x] Shopping cart endpoints (completed 2024-02-15)
- [x] Order creation and processing (completed 2024-02-16)
- [x] Payment gateway integration (Stripe) (completed 2024-02-18)
- [x] Order status tracking (completed 2024-02-19)
- [x] Order history functionality (completed 2024-02-20)
- [x] Email notifications for orders (completed 2024-02-21)
- [x] Refund processing system (completed 2024-02-22)
- [x] Admin order management interface (completed 2024-02-23)

## Phase 2: Frontend Development [IN PROGRESS] 🔄
### Task 2.1: React Application Setup [COMPLETED] ✅
- [x] Create React app with TypeScript (completed 2024-02-24)
- [x] Set up routing with React Router (completed 2024-02-25)
- [x] Configure state management (Redux Toolkit) (completed 2024-02-26)
- [x] Set up styling framework (Tailwind CSS) (completed 2024-02-27)
- [x] Configure build tools and bundling (completed 2024-02-28)
- [x] Set up development and production environments (completed 2024-03-01)
- [x] Configure linting and code formatting (completed 2024-03-02)
- [x] Set up unit testing framework (Jest/React Testing Library) (completed 2024-03-03)

### Task 2.2: User Interface Components [PARTIALLY COMPLETED] ⚠️
- [x] Header and navigation components (completed 2024-03-04)
- [x] Footer component (completed 2024-03-05)
- [x] Loading and spinner components (completed 2024-03-06)
- [x] Button and form input components (completed 2024-03-07)
- [x] Modal and dialog components (completed 2024-03-08)
- [x] Product card component (completed 2024-03-09)
- [ ] Shopping cart sidebar component (IN PROGRESS - 50% complete)
- [ ] User profile components (NOT STARTED)
- [ ] Admin dashboard components (NOT STARTED)
- [ ] Search and filter components (NOT STARTED)

### Task 2.3: Page Components [PARTIALLY COMPLETED] ⚠️
- [x] Home page layout (completed 2024-03-10)
- [x] Product listing page (completed 2024-03-11)
- [x] Product detail page (completed 2024-03-12)
- [x] User authentication pages (login/register) (completed 2024-03-13)
- [ ] Shopping cart page (IN PROGRESS - 30% complete)
- [ ] Checkout process pages (NOT STARTED)
- [ ] User profile and account pages (NOT STARTED)
- [ ] Order history and tracking pages (NOT STARTED)
- [ ] Admin product management pages (NOT STARTED)

### Task 2.4: API Integration [IN PROGRESS] 🔄
- [x] Set up Axios HTTP client (completed 2024-03-14)
- [x] Authentication API integration (completed 2024-03-15)
- [x] Product listing API integration (completed 2024-03-16)
- [x] Product detail API integration (completed 2024-03-17)
- [ ] Shopping cart API integration (IN PROGRESS - 60% complete)
- [ ] Order management API integration (NOT STARTED)
- [ ] User profile API integration (NOT STARTED)
- [ ] Search and filter API integration (NOT STARTED)

## Phase 3: Testing and Quality Assurance [NOT STARTED] ❌
### Task 3.1: Backend Testing
- [ ] Unit tests for all API endpoints
- [ ] Integration tests for database operations
- [ ] Authentication and authorization testing
- [ ] Payment processing testing
- [ ] Performance and load testing
- [ ] Security vulnerability testing
- [ ] API documentation with Swagger

### Task 3.2: Frontend Testing  
- [ ] Unit tests for React components
- [ ] Integration tests for user workflows
- [ ] End-to-end testing with Cypress
- [ ] Cross-browser compatibility testing
- [ ] Mobile responsiveness testing
- [ ] Accessibility testing (WCAG compliance)
- [ ] Performance optimization and testing

### Task 3.3: User Acceptance Testing
- [ ] Beta user testing program
- [ ] Feedback collection and analysis
- [ ] Bug tracking and resolution
- [ ] User experience improvements
- [ ] Performance optimization based on feedback

## Phase 4: Deployment and Production [NOT STARTED] ❌
### Task 4.1: Infrastructure Setup
- [ ] Set up production server environment
- [ ] Configure Docker containers
- [ ] Set up CI/CD pipeline with GitHub Actions
- [ ] Configure monitoring and logging (DataDog)
- [ ] Set up backup and disaster recovery
- [ ] SSL certificate configuration
- [ ] Domain name and DNS setup

### Task 4.2: Production Deployment
- [ ] Deploy backend API to production
- [ ] Deploy frontend to CDN (Cloudflare)
- [ ] Database migration to production
- [ ] Configure production environment variables
- [ ] Performance monitoring setup
- [ ] Error tracking and reporting setup

## Current Status Summary (As of March 18, 2024)
- **Backend**: 100% Complete ✅ (All APIs working and tested)
- **Frontend**: 60% Complete 🔄 (Core pages done, integration in progress)
- **Testing**: 0% Complete ❌ (Not started)
- **Deployment**: 0% Complete ❌ (Not started)

## Immediate Priorities (Next 2 weeks)
1. **HIGH**: Complete shopping cart page and API integration
2. **HIGH**: Implement checkout process pages
3. **MEDIUM**: Start user profile and account management
4. **MEDIUM**: Begin order history functionality
5. **LOW**: Start planning testing strategy

## Blockers and Issues
- Shopping cart state management needs refactoring (complex state updates)
- Payment processing testing requires sandbox environment setup
- Mobile UI needs responsive design improvements
- Performance optimization needed for product search

## Team Notes and Context
- Frontend developer: Working on cart integration, available full-time
- Backend developer: Available for frontend support, focusing on bug fixes
- Designer: Finalizing checkout flow mockups, available for consultation
- PM: Tracking toward March 31st launch date, considering scope reduction
"""

    completed_work_log = """# Completed Work Log - E-Commerce Project

## February 2024 Completions

### Week 1 (Feb 1-7)
- Email verification system implementation
- Role-based access control framework  
- Session management improvements
- OAuth2 Google integration
- OAuth2 Facebook integration
- Product CRUD endpoints
- Category management system

### Week 2 (Feb 8-14)
- Image upload and S3 storage integration
- Elasticsearch product search implementation
- Real-time inventory tracking system
- Dynamic pricing and discount engine
- Product reviews and ratings system
- Related products recommendation algorithm
- Shopping cart session management

### Week 3 (Feb 15-21)
- Shopping cart persistence and sync
- Order creation workflow
- Stripe payment gateway integration
- Order status tracking system
- Email notification templates
- Order history endpoint optimization
- Refund processing automation

### Week 4 (Feb 22-28)
- Admin order management dashboard
- React TypeScript project setup
- React Router configuration and lazy loading
- Redux Toolkit state management setup
- Tailwind CSS configuration and theming
- Webpack build optimization
- Development/production environment setup

## March 2024 Progress

### Week 1 (Mar 1-7)
- ESLint and Prettier configuration
- Jest and React Testing Library setup
- Header navigation with user state
- Footer with dynamic links
- Loading components with animations
- Form input validation components
- Modal system with portal rendering
- Product card responsive design

### Week 2 (Mar 8-14)
- Shopping cart sidebar (partial - state management complex)
- Home page hero section and featured products
- Product listing with pagination
- Product detail page with image gallery
- User authentication flow (login/register)
- Axios interceptors and error handling
- JWT token refresh mechanism

### Week 3 (Mar 15-21) [CURRENT]
- Product API integration with error boundaries
- Shopping cart API integration (in progress)
- Mobile responsive navigation
- Search functionality (frontend only)
- User session persistence improvements

## Technical Decisions Made
- Chose Redux Toolkit over Context API for complex state management
- Implemented optimistic UI updates for better user experience  
- Used React Query for server state management and caching
- Chose Tailwind over styled-components for faster development
- Implemented image lazy loading for performance
- Used React Hook Form for form validation and state
"""

    development_notes = """# Development Notes & Context

## Architecture Decisions
- **Backend**: Node.js with Express.js framework
- **Database**: PostgreSQL with Prisma ORM
- **Frontend**: React 18 with TypeScript
- **State Management**: Redux Toolkit + React Query
- **Styling**: Tailwind CSS with custom design system
- **Authentication**: JWT tokens with refresh token rotation
- **File Storage**: AWS S3 for product images
- **Payment**: Stripe payment processing
- **Email**: SendGrid for transactional emails
- **Search**: Elasticsearch for product search

## Key Implementation Details

### Authentication Flow
- JWT access tokens (15min expiry) + refresh tokens (7 day expiry)
- Automatic token refresh on API calls
- Secure HTTP-only cookies for refresh tokens
- Role-based permissions (user, admin, moderator)

### Product Management
- Hierarchical categories (max 3 levels deep)
- Multi-variant products (size, color, etc.)
- Real-time inventory tracking with reservation system
- Image optimization and CDN delivery
- Advanced search with filters, sorting, faceted navigation

### Order Processing
- Cart persistence across sessions
- Inventory reservation during checkout (15min expiry)
- Multi-step checkout with validation
- Payment intent creation before final submission
- Webhook handling for payment confirmations
- Automated email notifications for all order states

## Current Technical Challenges

### Shopping Cart Complexity
- Cart state synchronization between frontend and backend
- Handling price/availability changes during checkout
- Optimistic updates vs server validation
- Cart abandonment tracking and recovery

### Performance Considerations
- Product listing pagination (currently server-side)
- Image loading and optimization strategies
- Search result caching (Redis consideration)
- Database query optimization (N+1 problem in some areas)

### Mobile Experience
- Touch-friendly cart interactions
- Responsive product image galleries
- Mobile payment flow optimization
- Offline-first cart functionality (future consideration)

## Testing Strategy (Planned)
- Unit tests: 80%+ coverage target
- Integration tests: Critical user flows
- E2E tests: Complete purchase workflows  
- Performance tests: Load testing checkout flow
- Security tests: Authentication and payment flows

## Deployment Strategy (Planned)
- Docker containers for consistent deployment
- Blue-green deployment for zero downtime
- Automated database migrations
- CDN for static asset delivery
- Health checks and auto-recovery
- Monitoring and alerting setup
"""

    return {
        "main_project": main_project_file,
        "completed_log": completed_work_log, 
        "dev_notes": development_notes
    }

def create_realistic_mcp_context():
    """
    What an AI agent gets with MCP rolling work plan:
    Only incomplete items, with completion summaries for context
    """
    
    init_database()
    
    # Use a different project to avoid conflicts
    project_info = "https://github.com/test-user/ecommerce-platform"
    project_data = get_project_id(project_info)
    project_id = project_data["project_id"]
    
    # Create project with realistic completion state
    project_item_id = create_work_item(
        project_id, "project", "E-Commerce Platform Development", 
        "Full-stack e-commerce platform with React and Node.js", None
    )["id"]
    
    # Phase 1: Backend (COMPLETED) - will show as completion summary
    backend_phase_id = create_work_item(
        project_id, "phase", "Backend Development",
        "Complete backend implementation", project_item_id
    )["id"]
    
    # Add completed backend tasks (these will be summarized)
    tasks = [
        ("Database Design", "PostgreSQL schema and setup"),
        ("Authentication System", "JWT and OAuth implementation"),  
        ("Product Management API", "CRUD operations for products"),
        ("Order Management System", "Shopping cart and order processing")
    ]
    
    for task_title, task_desc in tasks:
        task_id = create_work_item(
            project_id, "task", task_title, task_desc, backend_phase_id
        )["id"]
        complete_item(task_id, project_id)
    
    # Complete the entire backend phase
    complete_item(backend_phase_id, project_id)
    
    # Phase 2: Frontend (IN PROGRESS) - will show incomplete items
    frontend_phase_id = create_work_item(
        project_id, "phase", "Frontend Development",
        "React-based user interface", project_item_id
    )["id"]
    
    # Task 2.1: React Setup (COMPLETED)
    react_setup_id = create_work_item(
        project_id, "task", "React Application Setup",
        "Initialize and configure React app", frontend_phase_id
    )["id"]
    complete_item(react_setup_id, project_id)
    
    # Task 2.2: UI Components (PARTIALLY COMPLETED)  
    ui_components_id = create_work_item(
        project_id, "task", "User Interface Components", 
        "Reusable React components", frontend_phase_id
    )["id"]
    
    # Some completed UI components
    completed_components = [
        "Header and navigation components",
        "Footer component", 
        "Loading and spinner components",
        "Button and form components",
        "Modal and dialog components",
        "Product card component"
    ]
    
    for comp in completed_components:
        comp_id = create_work_item(
            project_id, "subtask", comp, f"Component: {comp}", ui_components_id
        )["id"]
        complete_item(comp_id, project_id)
    
    # Incomplete UI components (these will show in rolling work plan)
    incomplete_components = [
        "Shopping cart sidebar component", 
        "User profile components",
        "Admin dashboard components",
        "Search and filter components"
    ]
    
    for comp in incomplete_components:
        create_work_item(
            project_id, "subtask", comp, f"Component: {comp}", ui_components_id
        )
    
    # Task 2.3: Page Components (PARTIALLY COMPLETED)
    page_components_id = create_work_item(
        project_id, "task", "Page Components",
        "Full page React components", frontend_phase_id  
    )["id"]
    
    # Incomplete page components
    incomplete_pages = [
        "Shopping cart page",
        "Checkout process pages", 
        "User profile and account pages",
        "Order history and tracking pages",
        "Admin product management pages"
    ]
    
    for page in incomplete_pages:
        create_work_item(
            project_id, "subtask", page, f"Page: {page}", page_components_id
        )
    
    # Task 2.4: API Integration (IN PROGRESS)
    api_integration_id = create_work_item(
        project_id, "task", "API Integration",
        "Connect frontend to backend APIs", frontend_phase_id
    )["id"]
    
    # Incomplete API integrations  
    incomplete_apis = [
        "Shopping cart API integration",
        "Order management API integration", 
        "User profile API integration",
        "Search and filter API integration"
    ]
    
    for api in incomplete_apis:
        create_work_item(
            project_id, "subtask", api, f"API: {api}", api_integration_id
        )
    
    # Phase 3: Testing (NOT STARTED)
    testing_phase_id = create_work_item(
        project_id, "phase", "Testing and Quality Assurance",
        "Comprehensive testing strategy", project_item_id
    )["id"]
    
    testing_tasks = [
        "Backend Testing",
        "Frontend Testing",
        "User Acceptance Testing"
    ]
    
    for task_title in testing_tasks:
        create_work_item(
            project_id, "task", task_title, f"Testing: {task_title}", testing_phase_id
        )
    
    # Phase 4: Deployment (NOT STARTED) 
    deployment_phase_id = create_work_item(
        project_id, "phase", "Deployment and Production",
        "Production deployment setup", project_item_id
    )["id"]
    
    deployment_tasks = [
        "Infrastructure Setup",
        "Production Deployment"
    ]
    
    for task_title in deployment_tasks:
        create_work_item(
            project_id, "task", task_title, f"Deployment: {task_title}", deployment_phase_id
        )
    
    # Get rolling work plan (only incomplete items with completion summaries)
    incomplete_items = get_work_items_for_project(project_id)
    all_items = get_all_work_items_for_project(project_id)
    hierarchy = build_hierarchy(incomplete_items)
    work_plan = add_completion_summaries(hierarchy, all_items)
    
    return work_plan, project_id

def run_realistic_comparison():
    """Run a realistic token usage comparison"""
    
    print("🚀 Realistic Token Usage Comparison Test")
    print("=" * 70)
    
    # Traditional approach: Full project context
    print("\n📁 Traditional approach - Full project context...")
    traditional_files = create_realistic_traditional_context()
    
    traditional_total = 0
    for filename, content in traditional_files.items():
        tokens = estimate_tokens(content)
        traditional_total += tokens
        print(f"  {filename}: {len(content):,} chars → {tokens:,} tokens")
    
    print(f"\n📊 Traditional total context: {traditional_total:,} tokens")
    
    # MCP approach: Rolling work plan only
    print("\n🔄 MCP approach - Rolling work plan only...")
    mcp_work_plan, project_id = create_realistic_mcp_context()
    
    mcp_json = json.dumps(mcp_work_plan, indent=2)
    mcp_tokens = estimate_tokens(mcp_json)
    
    print(f"  Rolling work plan: {len(mcp_json):,} chars → {mcp_tokens:,} tokens")
    
    # Calculate savings
    token_reduction = ((traditional_total - mcp_tokens) / traditional_total) * 100
    efficiency_multiplier = traditional_total / mcp_tokens
    
    print("\n" + "=" * 70)
    print("📈 REALISTIC RESULTS SUMMARY")
    print("=" * 70)
    print(f"Traditional full context:   {traditional_total:,} tokens")
    print(f"MCP rolling work plan:      {mcp_tokens:,} tokens")
    print(f"Token reduction:            {token_reduction:.1f}%")
    print(f"Efficiency multiplier:      {efficiency_multiplier:.1f}x")
    
    if token_reduction >= 80:
        print(f"✅ SUCCESS: Achieved {token_reduction:.1f}% token reduction!")
    elif token_reduction >= 50:
        print(f"⚠️  GOOD: {token_reduction:.1f}% reduction (target: 80%+)")
    else:
        print(f"❌ INSUFFICIENT: Only {token_reduction:.1f}% reduction")
    
    print(f"\n🔍 ANALYSIS:")
    print(f"• Traditional approach includes ALL project history and completed work")
    print(f"• MCP shows only {len([item for item in flatten_items(mcp_work_plan) if 'status' in item and item['status'] != 'completed'])} active work items")
    print(f"• Completed phases show as summaries (e.g., 'Backend Development: ✓ All tasks completed')")
    print(f"• Agent gets focused context on what needs attention NOW")
    print(f"• Massive reduction in cognitive load and context processing")
    
    return {
        "traditional_tokens": traditional_total,
        "mcp_tokens": mcp_tokens,
        "reduction_percentage": token_reduction,
        "efficiency_multiplier": efficiency_multiplier,
        "project_id": project_id
    }

def flatten_items(obj, items=None):
    """Helper to flatten nested structure for counting"""
    if items is None:
        items = []
    
    if isinstance(obj, dict):
        if 'id' in obj and 'type' in obj:
            items.append(obj)
        for value in obj.values():
            flatten_items(value, items)
    elif isinstance(obj, list):
        for item in obj:
            flatten_items(item, items)
    
    return items

if __name__ == "__main__":
    results = run_realistic_comparison()
    print(f"\n💾 Test completed. Project ID: {results['project_id']}")
