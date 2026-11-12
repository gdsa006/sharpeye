# Manage detective cases

Use the repository's **Actions** tab to manage a case:

1. Select **Manage detective case** and click **Run workflow**.
2. Choose **disable**, **enable**, or **delete**.
3. Enter the case's group ID, such as `group-002`, and run the workflow.
4. Wait for the management workflow and the Pages deployment to finish.

- **Disable** hides the case from the game but keeps its published files and on-device progress. Enable it later to restore access.
- **Enable** makes a disabled case available again.
- **Delete** removes the case entries and images from the published site. On the next successful game sync, the app removes its downloaded images and ad unlocks. To restore a deleted case, upload its ZIP again.

The app must include case-control support to apply these changes. Players receive a change the next time they open the game or tap **Sync** while online.
