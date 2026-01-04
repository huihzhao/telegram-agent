# How to Create the Notion Database 📚

Follow these steps exactly to set up your Notion integration.

## 1. Create a New Page
1.  Open Notion.
2.  Click **+ New Page** in the sidebar.
3.  Name it **"Telegram Tasks"**.
4.  Select **Table** from the options (or type `/table` and select "Table view").
5.  Click **+ New Database** (if asked).

## 2. Configure Properties (Columns)
The agent needs specific columns to put data in. Rename/Add them as follows:

| Property Name | Type | Value Options (Create these) |
| :--- | :--- | :--- |
| **Name** | Title | *(Default, just rename it)* |
| **Status** | Select | `Active` (Blue), `Done` (Green), `Rejected` (Red) |
| **Priority** | Number | *(or Select with 1-10)* |
| **Sender** | Text | |
| **Link** | URL | |
| **Deadline** | Text | *(or Date)* |

**How to add a property:**
1.  Click the `+` icon at the far right of the table header.
2.  Type the name (e.g., "Status").
3.  Select the **Type** (e.g., "Select").

## 3. Connect the Integration
**Crucial Step!** The Agent can't see the database unless you invite it.
1.  Open your **"Telegram Tasks"** database page.
2.  Click the **`...` (Three Dots)** in the top-right corner.
3.  Scroll down to **Connect to**.
4.  Search for and select your integration **"Telegram Agent"** (the one you made in the developer portal).
5.  Confirm the connection.

## 4. Get the Database ID
1.  Click the **Share** button (top right).
2.  Click **Copy link**.
3.  The link looks like this:
    `https://notion.so/myworkspace/`**`a8aec43384f447ed84390e8e42c2e089`**`?v=...`
4.  The **Database ID** is that 32-character code part between the `/` and the `?`.

## 5. Update .env
Copy that ID into your `.env` file:
```bash
NOTION_DATABASE_ID=a8aec43384f447ed84390e8e42c2e089
```
