# Terraform Jamf Pro Configuration Repository

This repository contains Terraform configurations for managing resources in Jamf Pro across multiple environments using the Jamf Pro Terraform provider. The workflows defined here automate the planning and application of Terraform configurations to your Jamf Pro environments, ensuring that your Jamf Pro settings are version-controlled and consistently applied.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Repository Structure](#repository-structure)
- [Environment Setup](#environment-setup)
- [Workflow Overview](#workflow-overview)
- [Branching Strategy](#branching-strategy)
- [GitHub Actions Workflows](#github-actions-workflows)
- [Drift Detection and Correction](#drift-detection-and-correction)
- [Example Terraform Resource](#example-terraform-resource)
- [Security and Best Practices](#security-and-best-practices)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Prerequisites

Before you begin, ensure you have the following prerequisites in place:

- **Jamf Pro Client Credentials**: A Jamf Pro client id and secret with appropriate API access is required. [client credentials](https://developer.jamf.com/jamf-pro/docs/client-credentials).
- **Terraform**: Terraform must be installed locally or available in your CI/CD environment. [Download Terraform](https://www.terraform.io/downloads.html).
- **Terraform Cloud**: An account on Terraform Cloud for managing Terraform state and running Terraform in a consistent environment. [Sign up for Terraform Cloud](https://app.terraform.io/signup/account).
- **GitHub Account**: A GitHub account for storing this repository and using GitHub Actions for automation. [Sign up for GitHub](https://github.com/join).

## Repository Structure

```
.
├── .github
│   └── workflows
│       ├── 00-hotfix.yml
│       ├── 01-terraform-plan-sandbox.yml
│       ├── 02-terraform-apply-sandbox.yml
│       ├── 03-release-and-plan-staging.yml
│       ├── 04-terraform-apply-staging.yml
│       ├── 05-release-and-plan-production.yml
│       ├── 06-terraform-apply-production.yml
│       ├── branch-cleanup.yml
│       ├── create-pr.yml
│       ├── create-version-and-release.yml
│       ├── drift.yml
│       ├── lint.yml
│       ├── send-notification.yml
│       ├── terraform-apply.yml
│       ├── terraform-plan.yml
│       └── update-release.yml
├── workload
│   ├── scripts
│   │   ├── hash_generator.py
│   │   └── version_determinator.py
│   └── terraform
│       └── jamfpro
│           ├── main.tf
│           ├── variables.tf
│           └── outputs.tf
├── README.md
└── .gitignore
```

## Environment Setup

This project supports three environments:

1. Sandbox
2. Staging
3. Production

Each environment has its own Terraform Cloud workspace:

- `terraform-jamfpro-sandbox`
- `terraform-jamfpro-staging`
- `terraform-jamfpro-production`

## Workflow Overview

1. Developers create short-lived branches prefixed with:
   - `feat-*`
   - `fix-*`
   - `docs-*`
   - `style-*`
   - `refactor-*`
   - `test-*`
   - `chore-*`
   - `build-*`
   - `ci-*`
   - `perf-*`
   
   This follows the [Conventional Commits](https://sentenz.github.io/convention/convention/conventional-commits/) specification for commit messages. These branches are merged into the `sandbox` branch for testing.

2. Changes are automatically checked for linting and formatting as well as Terraform planned against the Sandbox environment when pushed from these branches to sandbox by `01-terraform-plan-sandbox.yml`.

3. Once all desired changes have been tested, the short-lived branch is PR'd into the sandbox branch.
   Once merged into the sandbox branch, the changes are automatically applied to the Sandbox environment by `02-terraform-apply-sandbox.yml`.

4. Once the changes are applied to the Sandbox environment, promotion to Staging begins:
   a. The `03 - release and terraform plan to: staging` workflow is manually triggered from the sandbox branch.
   b. This workflow creates a new version and a new release branch (e.g., `release-v1.2.3`).
   c. It then generates a Terraform plan for the Staging environment using this release branch.
   d. A pull request is created from the release branch to the staging branch, with the plan for review.

5. After the pull request is reviewed and approved:
   a. The pull request is merged into the staging branch.
   b. This triggers the `04-terraform-apply-staging` workflow.
   c. The workflow checks that the merge is from a release branch (starting with `release-v`), then applies the Terraform changes to the Staging environment.
   d. After successful apply, the release branch is cleaned up (deleted).

6. The process for promoting to Production follows a similar pattern:
   a. A manual trigger of the `05 - release and terraform plan to: production` workflow is done from the staging branch.
   b. A new release branch is created for production promotion.
   c. After review and approval, the changes are applied to the Production environment.
   d. The production release branch is cleaned up after successful apply.
This approach ensures that each promotion to staging or production is associated with a specific release version, allowing for version tracking and potential rollback if needed.

## Branching Strategy

Our branching strategy consists of long-lived branches, short-lived feature branches, and temporary release branches. Here's a detailed breakdown:

| Branch Type | Branch Name | Purpose | Lifecycle |
|-------------|-------------|---------|-----------|
| Long-lived  | `sandbox`   | Represents the sandbox environment. All feature branches are merged here first. | Permanent |
| Long-lived  | `staging`   | Represents the staging environment. Release branches are merged here for testing before production. | Permanent |
| Long-lived  | `production` | Represents the production environment. Final destination for all changes. | Permanent |
| Short-lived | `feat-*`    | For developing new features | Merged to `sandbox` when complete, then deleted |
| Short-lived | `fix-*`     | For fixing bugs | Merged to `sandbox` when complete, then deleted |
| Short-lived | `docs-*`    | For documentation updates | Merged to `sandbox` when complete, then deleted |
| Short-lived | `style-*`   | For code style changes (formatting, missing semi colons, etc.) | Merged to `sandbox` when complete, then deleted |
| Short-lived | `refactor-*`| For code refactoring | Merged to `sandbox` when complete, then deleted |
| Short-lived | `test-*`    | For adding or updating tests | Merged to `sandbox` when complete, then deleted |
| Short-lived | `chore-*`   | For routine tasks or maintenance | Merged to `sandbox` when complete, then deleted |
| Short-lived | `build-*`   | For changes that affect the build system or external dependencies | Merged to `sandbox` when complete, then deleted |
| Short-lived | `ci-*`      | For changes to CI configuration files and scripts | Merged to `sandbox` when complete, then deleted |
| Short-lived | `perf-*`    | For performance improvements | Merged to `sandbox` when complete, then deleted |
| Temporary   | `release-v*` | Created for each release to staging or production | Created during release process, used for final review and applying changes, then deleted after successful apply |

### Branch Flow

```shell
Time ----->

 feat-*  
 fix-*    
 docs-*          release-v1.0.0            release-v1.1.0
 style-*         (sandbox to staging)      (staging to production)
 refactor-*            |                          |
 test-*                |                          |
 ci-*                  |                          |
 chore-*               |                          |
   |                   |                          |
   v                   v                          v
+--------+        +--------+                 +--------+
|        |        |        |                 |        |
| Sandbox|------->| Sandbox|---------------->| Sandbox|  (Default branch)
|        |        |        |                 |        |
+--------+        +--------+                 +--------+
     ^                 | PR                       | PR
     |                 |                          |
     |                 +                          +
     |            +--------+                 +--------+ 
     |            |        |                 |        |
     +------------| Staging|---------------->| Staging|
     |            |        |                 |        |
     |            +--------+                 +--------+
     |                 ^                          | PR
     |                 |                          |
     |                 |                          +
     |                 |                    +----------+
     |                 |                    |          |
     +-----------------+---------------====>|Production|
                       .                    |          |
                       .                    +----------+
                       .
                       +---> Branch deleted after merge

 Legend:
 -----> : Git Flow
 -----+ : Pull Request
 ====> : Hotfix Flow (when needed)
 ...   : Branch deletion
```

### Notes

- Hotfixes may bypass the normal flow in emergencies, but should be backported to ensure all environments stay in sync.
- Release branches (`release-v*`) are temporary and serve as a stable point for final testing and deployment. They are deleted after successful merge and apply.
- Long-lived branches (`sandbox`, `staging`, `production`) should never be deleted and represent the state of each environment.

## GitHub Actions Workflows

1. **Terraform Apply to Sandbox** (`01-terraform-sandbox.yml`)
   - Triggered on push to branches prefixed with `feature-`, `bugfix-`, `hotfix-`, `chore-`, `config-`, `docs-`, or `test-`
   - Also can be manually triggered with a specified branch name
   - Applies changes directly to the Sandbox environment using Terraform Cloud
   - Validates branch name for manual runs
   - Uses the `terraform-jamfpro-sandbox` workspace in Terraform Cloud

Getting Started

1. **Create a New Repository**: Start by creating a new repository in your GitHub account.
2. **Clone and Push to Your New Repository**: Clone this template repository and push it to your newly created repository:

```bash
git clone https://github.com/original-owner/terraform-jamfpro-config-template.git
cd terraform-jamfpro-config-template
git remote set-url origin https://github.com/your-username/your-new-repo.git
git push -u origin main
```

Replace original-owner with the username of the template repository owner, and your-username and your-new-repo with your GitHub username and the name of your new repository.

3. **Configure Github Secrets**: Set up the following secrets in your GitHub repository settings:

- `TF_API_TOKEN`: Your Terraform Cloud API token for Terraform Cloud backend.
- `PAT_TOKEN`: Your GitHub Personal Access Token for branch management operations.

To set up the PAT_TOKEN:
a. Go to your GitHub Settings > Developer settings > Personal access tokens > Fine-grained tokens.
b. Click "Generate new token".
c. Give your token a descriptive name, e.g., "Terraform Jamf Pro Config Branch Management".
d. Set the expiration as per your security policies.
e. Under "Repository access", select "Only select repositories" and choose the repository you're setting up.
f. Under "Permissions", grant the following permissions:
- Repository permissions:
- Contents: Read and write (This allows branch management)
- Metadata: Read-only (This is required for API operations)
- Organization permissions:
- Members: Read-only (If working within an organization)
g. Click "Generate token" and copy the token immediately.
h. In your repository, go to Settings > Secrets and variables > Actions.
i. Click "New repository secret", name it PAT_TOKEN, and paste your token as the value.

Optional:

- `MSTEAMS_WEBHOOK_URL`: Your Microsoft Teams webhook URL for sending notifications.
- `SLACK_WEBHOOK_URL`: Your Slack webhook URL for sending notifications.

To set up the notification webhooks:

a. For Microsoft Teams:

- In your Teams channel, click the '...' next to the channel name and select 'Connectors'.
- Find 'Incoming Webhook' and click 'Configure'.
- Provide a name for your webhook and optionally upload an image.
- Click 'Create' and copy the webhook URL provided.
- In your GitHub repository, go to Settings > Secrets and variables > Actions.
- Click "New repository secret", name it MSTEAMS_WEBHOOK_URL, and paste the webhook URL as the value.

b. For Slack:

- Go to your Slack workspace's App Directory and create a new app (or use an existing one).
- Under 'Features', select 'Incoming Webhooks' and activate them.
- Click 'Add New Webhook to Workspace' and select the channel for notifications.
- Copy the webhook URL provided.
- In your GitHub repository, go to Settings > Secrets and variables > Actions.
- Click "New repository secret", name it SLACK_WEBHOOK_URL, and paste the webhook URL as the value.

These webhook URLs are used in the Send Notification workflow (send-notification.yml) to send deployment status updates to your team. The workflow determines which service to use based on the notification_channel input. Here's a snippet of how it's used:

4. **Configure Terraform Cloud Secrets**: Set up the following secrets in your Terraform Cloud workspace variable settings for each environment (Sandbox, Staging, Production):
    - `JAMFPRO_INSTANCE_FQDN`: Your Jamf Pro instance URL. For example: `https://your-instance.jamfcloud.com`.
    - `JAMFPRO_AUTH_METHOD`: Can be either `basic` or `oauth2`.
    - `JAMFPRO_CLIENT_ID`: Your Jamf Pro client id when `JAMFPRO_AUTH_METHOD` is set to 'oauth2'.
    - `JAMFPRO_CLIENT_SECRET`: Your Jamf Pro client secret when `JAMFPRO_AUTH_METHOD` is set to 'oauth2'.
    - `JAMFPRO_BASIC_AUTH_USERNAME`: Your Jamf Pro username when `JAMFPRO_AUTH_METHOD` is set to 'basic'.
    - `JAMFPRO_BASIC_AUTH_PASSWORD`: Your Jamf Pro user password when `JAMFPRO_AUTH_METHOD` is set to 'basic'.

   Note: For Terraform Cloud, when setting variables you do not need to prefix your env vars with `TF_VAR_` as Terraform Cloud automatically does this for you. Additionally, ensure to select the variable category as `Terraform variable`, with the HCL tickbox unchecked.

4. **Update Terraform Variables**: Modify the `terraform` block in your `.tf` files to match your Jamf Pro instance details. For example:

   ```hcl
   provider "jamfpro" {
     jamfpro_instance_fqdn                = var.jamfpro_instance_fqdn
     jamfpro_load_balancer_lock           = var.jamfpro_jamf_load_balancer_lock
     auth_method                          = var.jamfpro_auth_method
     client_id                            = var.jamfpro_client_id
     client_secret                        = var.jamfpro_client_secret
     log_level                            = var.jamfpro_log_level
     log_output_format                    = var.jamfpro_log_output_format
     log_console_separator                = var.jamfpro_log_console_separator
     log_export_path                      = var.jamfpro_log_export_path
     export_logs                          = var.jamfpro_export_logs
     hide_sensitive_data                  = var.jamfpro_hide_sensitive_data
     token_refresh_buffer_period_seconds  = var.jamfpro_token_refresh_buffer_period_seconds
     mandatory_request_delay_milliseconds = var.jamfpro_mandatory_request_delay_milliseconds
   }
   ```

   It's strongly recommended for beginners to ensure that `jamfpro_load_balancer_lock` is set to true, to avoid any issues with the Jamf Pro load balancer.

5. **Backend Configuration**: For our multi-environment setup, we'll be using Terraform workspaces. This approach allows us to use a single set of configuration files while maintaining separate states for each environment. Here's how to structure it:

   In your main Terraform configuration file (e.g., `main.tf`):

   ```hcl
    terraform {
      cloud {
        organization = "deploymenttheory"
        workspaces {
          tags = ["Jamf Pro"]
        }
      }
    }
   ```

   This configuration tells Terraform to use Terraform Cloud with the "deploymenttheory" organization and to work with any workspace tagged with "jamfpro".

   In Terraform Cloud:
   1. Create three workspaces:
      - `terraform-jamfpro-sandbox`
      - `terraform-jamfpro-staging`
      - `terraform-jamfpro-production`
   2. Tag each of these workspaces with the "jamfpro" tag.
   3. Set workspace-specific variables in Terraform Cloud for each environment. For example, you might have a variable `environment` set to "sandbox", "staging", or "production" in the respective workspaces.

   In your Terraform configuration, you can then use these workspace-specific variables to customize resources for each environment. For example:

   ```hcl
   resource "jamfpro_building" "example" {
     name = "Building-${var.environment}"
     // other attributes...
   }
   ```

   This approach ensures that each environment has its own isolated state in Terraform Cloud while allowing you to use a single set of configuration files. It provides flexibility in managing environment-specific configurations through Terraform Cloud workspace variables.

   Remember to set up appropriate access controls and variable values for each workspace in Terraform Cloud to maintain proper separation between environments.

6. **Terraform Provider Configuration**: Specify the provider source and version:

   ```hcl
   terraform {
     required_providers {
       jamfpro = {
         source  = "deploymenttheory/jamfpro"
         version = "0.1.12"
       }
     }
   }
   ```

7. **Define Your Resources**: Use Terraform resource definitions to manage your Jamf Pro resources.

8. **Create a New Branch**: Create a new branch with the appropriate prefix eg. (`feature-`, `bugfix-`, or `chore-`).

9. **Make Changes and Push**: Make your changes and push to GitHub.

10. **Test in Sandbox**: The `01 - terraform testing: sandbox` workflow will automatically run.

11. **Promote to Sandbox**: After testing in Sandbox, create a pull request to merge all chanages from your short lived branch into the `sandbox` branch.

12. **Promote to Staging**: Now manually trigger the `02-release-and-plan-staging.yml` workflow and approve the pull request to merge the release branch into the `staging` branch after change review.

13. **Apply to Staging**: After the pull request is merged, the `03-terraform-apply-staging.yml` workflow will automatically run to apply the changes to the Staging environment.

14. **Promote to Production**: Repeat the process for promoting to Production by manually triggering the `04-release-and-plan-production.yml` workflow and approving the pull request to merge the release branch into the `production` branch after change review.

15. **Apply to Production**: After the pull request is merged, the `05-terraform-apply-production.yml` workflow will automatically run to apply the changes to the Production environment.


## Drift Detection and Correction

The `drift-detection-correction.yml` workflow runs nightly to detect and correct any drift in your environments:

- Checks for drift in Sandbox, Staging, and Production environments
- Automatically corrects drift if detected
- Sends notifications (configure as needed)

## Example Terraform Resource

Below is an example of defining a building in Jamf Pro using Terraform:

```hcl
resource "jamfpro_building" "example_building" {
  name            = "Example Building"
  street_address1 = "123 Example St"
  street_address2 = "Suite 100"
  city            = "Example City"
  state_province  = "Example State"
  zip_postal_code = "12345"
  country         = "Example Country"
}
```

## Security and Best Practices

- Use Terraform Cloud for secure state management
- Implement branch protection rules for `staging` and `production` branches
- Review all plans before applying changes
- Use least-privilege principle for API credentials
- Ensure sensitive data like `client_secret` is marked as sensitive in Terraform and securely stored in GitHub Secrets
- Always review Terraform plans before merging into the main branch to prevent unintended changes
- Limit access to the GitHub repository and associated secrets to authorized personnel only

## Troubleshooting

- Check GitHub Actions logs for detailed error messages
- Verify Terraform Cloud workspace configurations
- Ensure Jamf Pro API credentials are correct and have necessary permissions

## Contributing

1. Fork the repository
2. Create a new branch with the appropriate prefix
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.