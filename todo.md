# Subscription Management System --- Team TODO

> A practical working checklist for building the Brightloop subscription
> platform.\
> The goal is not just to finish features quickly, but to build
> something clean, reliable, easy to use, and easy to explain during the
> Odoo Hackathon review.

## Team responsibilities

  -----------------------------------------------------------------------
  Team member             Main responsibility     What this includes
  ----------------------- ----------------------- -----------------------
  **Nijoy**               Django backend and      Project setup, Django
                          overall structure       apps, backend
                                                  architecture, models
                                                  integration, APIs,
                                                  business logic,
                                                  authentication flow,
                                                  and keeping the system
                                                  modular

  **Nivin**               Frontend and web        UI/UX, responsive
                          development             pages, navigation,
                                                  forms, dashboards,
                                                  customer portal, API
                                                  integration, and
                                                  frontend error/loading
                                                  states

  **Manav**               Database design and     Database selection and
                          schemas                 setup, ER design,
                                                  Django model/schema
                                                  planning,
                                                  relationships,
                                                  constraints,
                                                  migrations, indexes,
                                                  and query efficiency

  **Albin**               Validation and software Input validation test
                          testing                 cases, functional
                                                  testing, edge cases,
                                                  regression testing, bug
                                                  tracking, security
                                                  checks, and final test
                                                  pass
  -----------------------------------------------------------------------

These are ownership areas, not silos. Everyone should understand the
full flow, review each other's work, and contribute to GitHub.

------------------------------------------------------------------------

## 1. Before we start

-   [ ] Read the problem statement together and agree on what the first
    complete version must do.
-   [ ] List the main user roles: **Admin, Internal Staff, and
    Customer**.
-   [ ] Agree on the tech stack. Use a local relational database such as
    **PostgreSQL or MySQL** rather than relying on a
    Backend-as-a-Service platform.
-   [ ] Decide the API contract between Django and the frontend before
    building pages around assumptions.
-   [ ] Sketch the main screens and the database relationships.
-   [ ] Create the GitHub repository and add all four members.
-   [ ] Agree on branch names, commit message style, and how pull
    requests will be reviewed.
-   [ ] Create a shared issue/task board and assign owners.
-   [ ] Set up a `.env.example`; keep real secrets and credentials out
    of Git.
-   [ ] Add a README with setup instructions so every team member can
    run the project locally.

**Owners** - Nijoy: Django project structure and backend setup. - Nivin:
initial page flow and UI direction. - Manav: database choice, ER
diagram, and schema draft. - Albin: test plan outline and acceptance
checklist.

## 2. Project foundation

### Backend and architecture --- Nijoy

-   [ ] Create the Django project and configure the development
    environment.
-   [ ] Split the project into focused apps/modules instead of putting
    everything in one file or app.
-   [ ] Set up environment-based configuration for database credentials,
    secret keys, email settings, and debug mode.
-   [ ] Configure Django REST Framework (if selected) and establish
    consistent API response patterns.
-   [ ] Add a clear separation between models, serializers, views,
    permissions, and business logic.
-   [ ] Set up authentication and role-based permissions.
-   [ ] Add basic logging and a consistent error-handling approach.
-   [ ] Document how to start the backend and run migrations.

### Database and schemas --- Manav

-   [ ] Finalise PostgreSQL/MySQL setup and share the local setup steps.
-   [ ] Prepare an ER diagram before finalising the models.
-   [ ] Identify the core entities and their relationships:
    -   Users and roles
    -   Customers and staff profiles
    -   Products and product variants
    -   Plans and plan availability
    -   Taxes and tax rules
    -   Quotations and quotation templates
    -   Subscriptions and subscription lines
    -   Discounts and discount rules
    -   Invoices and invoice lines
    -   Payments
-   [ ] Define primary keys, foreign keys, unique constraints, required
    fields, and sensible defaults.
-   [ ] Decide how money, percentages, quantities, dates, and billing
    intervals will be stored.
-   [ ] Add indexes for fields used often in lookups and filters.
-   [ ] Review delete/update behaviour so important billing history is
    not accidentally lost.
-   [ ] Coordinate schema changes with Nijoy and keep migrations
    committed to Git.

### Frontend foundation --- Nivin

-   [ ] Set up the frontend project and agree on its folder structure.
-   [ ] Create a consistent design system: colours, typography, spacing,
    buttons, inputs, tables, and status indicators.
-   [ ] Build the application shell with sidebar/top navigation and
    responsive layout.
-   [ ] Create reusable form fields, modals, tables, cards, alerts, and
    loading states.
-   [ ] Set up the API client and centralise the backend base URL.
-   [ ] Add route protection and role-aware navigation.
-   [ ] Make sure every page has useful empty, loading, success, and
    error states.

### Quality foundation --- Albin

-   [ ] Prepare a test checklist from the problem statement.
-   [ ] Define the expected behaviour for each user role.
-   [ ] Prepare valid, invalid, boundary, and duplicate input cases.
-   [ ] Agree with the team on what must pass before a feature is marked
    complete.
-   [ ] Check that tests can be run consistently on each developer's
    machine.

## 3. Build the core features

### A. Accounts, login, and access control

-   [ ] Customer can create an account using an email and password.
-   [ ] Enforce unique email addresses.
-   [ ] Password must be more than 8 characters and contain uppercase,
    lowercase, and a special character.
-   [ ] Add login and logout.
-   [ ] Add password reset through a link sent to the registered email.
-   [ ] Admin has access to the full system.
-   [ ] Internal staff have limited access based on their role.
-   [ ] Customers can access only their own subscriptions and invoices.
-   [ ] Only the admin can create/add staff members.

**Owners:** Nijoy --- authentication and permissions; Nivin --- screens
and form feedback; Manav --- user/role schema; Albin --- access and
validation tests.

### B. Products, variants, and plans

-   [ ] Admin can create, view, update, and manage products.
-   [ ] Product stores its name, type, sales price, cost price, and
    notes.
-   [ ] Support product variants (for example, brand).
-   [ ] Variant selections can adjust the product price where
    applicable.
-   [ ] Admin can create plans with price and billing interval.
-   [ ] Support daily, weekly, monthly, and yearly billing intervals.
-   [ ] Store minimum quantity and plan availability dates.
-   [ ] Support plan settings for automatic closure, early closure,
    pause, and renewal.
-   [ ] Validate prices, dates, quantities, and required fields.

**Owners:** Nijoy --- product/plan logic and APIs; Nivin --- admin
screens; Manav --- product, variant, and plan schemas; Albin --- pricing
and date edge cases.

### C. Quotations and subscriptions

-   [ ] Create quotation templates with predefined plans and product
    lines.
-   [ ] Set a validity period for each quotation template.
-   [ ] Create a quotation for a customer using a template.
-   [ ] Give every subscription a unique number.
-   [ ] Store customer, plan, start date, expiry date, and payment
    terms.
-   [ ] Support subscription lines with product, quantity, unit price,
    taxes, and amount.
-   [ ] Implement the subscription lifecycle:
    -   [ ] Draft
    -   [ ] Quotation
    -   [ ] Confirmed
    -   [ ] Active
    -   [ ] Closed
-   [ ] Make the current status clear to staff and customers where
    appropriate.
-   [ ] Validate allowed status transitions; prevent invalid state
    changes.

**Owners:** Nijoy --- workflow and APIs; Nivin ---
quotation/subscription pages; Manav --- related schemas and
relationships; Albin --- lifecycle and transition tests.

### D. Invoices and recurring billing

-   [ ] Generate invoices from subscriptions when they are due.
-   [ ] Pre-fill customer details, product lines, taxes, and totals.
-   [ ] Calculate taxes using admin-configured rules.
-   [ ] Support invoice actions: confirm, cancel, send, and print.
-   [ ] Implement invoice states:
    -   [ ] Draft
    -   [ ] Confirmed
    -   [ ] Paid
-   [ ] Make recurring invoice generation safe to run more than once.
-   [ ] Prevent duplicate invoices for the same subscription billing
    period.
-   [ ] Make sure due invoices are not silently skipped.
-   [ ] Show the next billing date and invoice history where relevant.

**Owners:** Nijoy --- billing logic and invoice APIs; Nivin --- invoice
screens and actions; Manav --- invoice schema, constraints, and indexes;
Albin --- duplicate billing, skipped billing, and calculation tests.

### E. Discounts

-   [ ] Only admin can create and manage discount rules.
-   [ ] Support fixed-amount and percentage discounts.
-   [ ] Support minimum purchase amount or minimum quantity.
-   [ ] Add start date, end date, and usage limit.
-   [ ] Allow a discount to apply to selected products or an entire
    subscription.
-   [ ] Apply eligible discounts automatically to the next invoice.
-   [ ] Stop applying discounts when they expire or reach their usage
    limit.
-   [ ] Validate discount values and prevent invalid combinations.

**Owners:** Nijoy --- discount rules and invoice integration; Nivin ---
discount management UI; Manav --- discount schema and usage tracking;
Albin --- eligibility, expiry, and usage-limit tests.

### F. Payments

-   [ ] Record each payment against the correct invoice.
-   [ ] Store payment method, amount, date, and note.
-   [ ] Support recording payments made through different methods.
-   [ ] Update invoice payment status correctly.
-   [ ] Show paid and outstanding invoices clearly.
-   [ ] Make it easy for staff to identify overdue invoices.
-   [ ] Handle partial payments only if the team has time and the data
    model supports them cleanly.

**Owners:** Nijoy --- payment and invoice status logic; Nivin ---
payment entry and invoice views; Manav --- payment schema and invoice
relationship; Albin --- amount matching and payment status tests.

### G. Dashboard and reporting

-   [ ] Show the number of active subscriptions.
-   [ ] Show revenue received.
-   [ ] Show outstanding amounts.
-   [ ] Show overdue invoices.
-   [ ] Add useful filters and a clear summary view.
-   [ ] Make dashboard values come from live database data, not
    hard-coded JSON.
-   [ ] Check that totals match the underlying invoices and payments.

**Owners:** Nijoy --- reporting endpoints and aggregation; Nivin ---
dashboard UI and filters; Manav --- query/index review; Albin --- verify
figures against sample records.

### H. Customer portal

-   [ ] Customer can view their own profile/account details.
-   [ ] Customer can view their subscriptions and current statuses.
-   [ ] Customer can view invoices and payment status.
-   [ ] Customer must never be able to access another customer's records
    by changing an ID or URL.
-   [ ] Keep the portal simple and easy to navigate.

**Owners:** Nijoy --- customer-scoped APIs and permissions; Nivin ---
portal UI; Manav --- ownership relationships; Albin --- cross-customer
access tests.

## 4. Validation, security, and reliability

-   [ ] Validate data on the backend even when frontend validation
    exists.
-   [ ] Show clear, human-readable error messages instead of raw server
    errors.
-   [ ] Test empty fields, invalid email addresses, weak passwords,
    negative prices, invalid quantities, and incorrect dates.
-   [ ] Check permissions for every sensitive API endpoint.
-   [ ] Ensure customers cannot view or modify another customer's data.
-   [ ] Protect secrets and credentials using environment variables.
-   [ ] Avoid exposing stack traces or sensitive information in
    production responses.
-   [ ] Check that invoice totals, taxes, discounts, and payments are
    calculated consistently.
-   [ ] Test duplicate requests and repeated billing runs.
-   [ ] Add database transactions around operations that must succeed or
    fail together.
-   [ ] Review important changes through pull requests.

## 5. Git and team collaboration

-   [ ] Every member works on their own feature branch.
-   [ ] Do not commit directly to `main`.
-   [ ] Use descriptive commit messages (for example,
    `feat: add subscription creation API`).
-   [ ] Push work regularly; don't wait until the end to upload
    everything.
-   [ ] Open pull requests for completed features.
-   [ ] Ask at least one teammate to review important changes.
-   [ ] Pull the latest changes before starting new work.
-   [ ] Resolve merge conflicts together rather than overwriting another
    person's work.
-   [ ] Keep `.env`, passwords, API keys, local databases, and generated
    secrets out of the repository.
-   [ ] Keep README and setup instructions updated as the project
    changes.

## 6. Final testing and hackathon readiness

### Functional testing --- Albin leads

-   [ ] Test the full journey: customer signup → product/plan setup →
    quotation → subscription activation → invoice generation → payment →
    dashboard.
-   [ ] Test each role separately: Admin, Staff, and Customer.
-   [ ] Test expired plans, paused subscriptions, early closures,
    renewals, and invalid status changes.
-   [ ] Test discount start/end dates and usage limits.
-   [ ] Test tax and invoice calculations with known sample values.
-   [ ] Test overdue invoice identification.
-   [ ] Test that repeated billing runs do not create duplicate
    invoices.
-   [ ] Retest fixed bugs to avoid regressions.
-   [ ] Keep a short list of known limitations rather than hiding
    unfinished behaviour.

### UI and usability --- Nivin leads

-   [ ] Check all pages for consistent spacing, colours, typography, and
    layout.
-   [ ] Check navigation labels and page flow.
-   [ ] Test forms, tables, filters, modals, and action buttons.
-   [ ] Check responsive behaviour at common laptop and mobile widths.
-   [ ] Make statuses and important actions easy to understand.
-   [ ] Ensure errors and success messages are visible and helpful.

### Backend and database review --- Nijoy and Manav lead

-   [ ] Review API structure and remove duplicated business logic.
-   [ ] Check model relationships, constraints, and migrations.
-   [ ] Check common queries and add indexes where justified.
-   [ ] Confirm the application uses real database records throughout.
-   [ ] Test with a realistic amount of sample data.
-   [ ] Profile slow pages and queries; aim to keep pages responsive,
    with the brief's target of under two seconds even with thousands of
    subscriptions.
-   [ ] Check that setup works from a fresh clone.

### Demo preparation --- everyone

-   [ ] Prepare realistic sample data for the demo.
-   [ ] Make sure the demo environment is stable and the main flow
    works.
-   [ ] Prepare a short explanation of the architecture and why the
    database is structured this way.
-   [ ] Be ready to explain key API endpoints, validation rules,
    permissions, and billing logic.
-   [ ] Each person should explain the part they worked on.
-   [ ] Walk through the project together once before presenting.
-   [ ] Be honest about what is implemented, what is partially
    implemented, and what is planned next.

------------------------------------------------------------------------

## 7. Suggested order of work

To avoid everyone building against changing assumptions, work in this
order:

1.  **Agree on scope and data model** --- all four; Manav owns the
    schema draft.
2.  **Set up the backend and frontend foundations** --- Nijoy and Nivin,
    in parallel.
3.  **Connect the database and authentication** --- Nijoy and Manav,
    with Nivin integrating the screens.
4.  **Build products, plans, quotations, and subscriptions** --- split
    across the four ownership areas.
5.  **Build invoices, recurring billing, discounts, and payments** ---
    prioritise correctness over visual polish.
6.  **Build the customer portal and reporting dashboard** --- use real
    API data.
7.  **Run end-to-end tests, fix issues, and prepare the demo** ---
    everyone; Albin coordinates testing.

## 8. What we should not compromise on

-   **Database design:** This is a major evaluation area. Keep the
    schema relational, understandable, and consistent.
-   **Real data:** Static JSON can help during early UI work, but the
    final application should use live database-backed APIs.
-   **Validation:** Validate on both frontend and backend, and explain
    errors clearly.
-   **Modularity:** Keep code organised by responsibility and feature.
-   **Security:** Enforce roles and customer-level data access on the
    backend, not just by hiding frontend links.
-   **Performance:** Avoid unnecessary queries and check dashboard/list
    pages with realistic data.
-   **Git teamwork:** All four members should contribute through
    meaningful commits and reviewed changes.
-   **Shared ownership:** Everyone should understand the overall system
    well enough to participate in the presentation.

------------------------------------------------------------------------

## Team check-in

At the end of each work session, quickly update:

-   [ ] What did I finish?
-   [ ] What am I working on next?
-   [ ] Am I blocked by another feature, API, or schema decision?
-   [ ] Have I pushed my latest changes?
-   [ ] Is there anything the rest of the team needs to review?

**Definition of done:** A task is complete when the feature works with
real data, handles invalid input gracefully, respects permissions, has
been tested, and is pushed to GitHub with enough context for another
teammate to understand it.
