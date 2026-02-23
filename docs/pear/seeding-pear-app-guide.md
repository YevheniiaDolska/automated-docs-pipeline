---
title: "Seeding a Pear application"
description: "Make your Pear app available on the P2P network by announcing to the DHT, accepting peer connections, and sharing files directly."
content_type: how-to
tags:
  - Pear
  - Seeding
  - DHT
  - P2P
  - Hyperswarm
---

# Seeding a Pear application

Seeding makes your Pear application available to other users on the peer-to-peer network. The `pear seed` command announces your app to the DHT (Distributed Hash Table) and keeps it accessible while the seeding process runs.

```bash
pear seed dev
```

```
🍐 Seeding: my-chat-app [ dev ]
   ctrl^c to stop & exit

-o-:-
    pear://keet4yc8x5dat5n49wmkrkofwxbfrs9mmow4udpj7yjpgcsp15qo
...
^_^ announced
```

After completing this guide, you will have a running seed that other peers can connect to and download your application from.

## Prerequisites

### Required software

| Software | Version | Check command |
|----------|---------|---------------|
| Pear Runtime | Latest | `pear --version` |
| Node.js | 18+ | `node --version` |

Install Pear Runtime if you have not already:

```bash
npm install -g pear
```

Verify installation:

```bash
pear --version
```

Expected output:

```
pear version 1.x.x
```

### Required files

Your project must have a `package.json` with a name field:

```json
{
  "name": "my-chat-app",
  "main": "index.html",
  "pear": {
    "name": "my-chat-app",
    "type": "desktop"
  }
}
```

### Prior steps completed

Before seeding, you must have:

1. Created a Pear project (`pear init`)
1. Built your application (index.html, app.js, etc.)
1. Tested locally (`pear run .`)

## How seeding works

When you run `pear seed`, three things happen:

1. **Announce:** Your app's public key registers on the DHT (a global distributed directory)
1. **Listen:** Your machine starts accepting connections from other peers
1. **Share:** When peers request your app, you send them the files

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   You       │         │    DHT      │         │   Peer      │
│  (seeder)   │         │  (network)  │         │  (user)     │
└──────┬──────┘         └──────┬──────┘         └──────┬──────┘
       │                       │                       │
       │  1. Announce key      │                       │
       │──────────────────────>│                       │
       │                       │                       │
       │                       │  2. Lookup key        │
       │                       │<──────────────────────│
       │                       │                       │
       │                       │  3. Return your IP    │
       │                       │──────────────────────>│
       │                       │                       │
       │  4. Direct P2P connection                     │
       │<──────────────────────────────────────────────│
       │                       │                       │
       │  5. Send app files                            │
       │──────────────────────────────────────────────>│
```

The DHT does not store your app. It only stores a mapping from your app's public key to your IP address. Your machine sends the actual files directly to peers.

## Step-by-step instructions

### Step 1: Stage your application

Staging copies your local files to a Hyperdrive (distributed storage format). Run this from your project directory:

```bash
pear stage dev
```

Expected output:

```
ℹ Staging: my-chat-app [ dev ]

  pear://keet4yc8x5dat5n49wmkrkofwxbfrs9mmow4udpj7yjpgcsp15qo

  Staged 5 files (2.4 KB)
  Length: 1
```

**What each line means:**

| Output | Meaning |
|--------|---------|
| `pear://keet4yc...` | Your app's unique link. Save this because you will share it with users. |
| `Staged 5 files` | Number of files copied to the Hyperdrive |
| `Length: 1` | Version number (increments with each staging) |

**Why this matters:** Staging creates a versioned snapshot. Peers receive this exact version, ensuring consistency.

### Step 2: Start seeding

Run the seed command to make your staged app available:

```bash
pear seed dev
```

Expected output:

```
🍐 Seeding: my-chat-app [ dev ]
   ctrl^c to stop & exit

-o-:-
    pear://keet4yc8x5dat5n49wmkrkofwxbfrs9mmow4udpj7yjpgcsp15qo
...
^_^ announced
```

**What each line means:**

| Output | Meaning |
|--------|---------|
| `ctrl^c to stop & exit` | Seeding runs until you press Ctrl+C |
| `^_^ announced` | Your app is now discoverable on the DHT |

**Keep this terminal open.** Closing it stops seeding, and peers cannot find your app.

### Step 3: Verify seeding is active

Open a new terminal window (keep the seeding terminal running) and check your app info:

```bash
pear info dev
```

Expected output:

```
ℹ Info: my-chat-app [ dev ]

  pear://keet4yc8x5dat5n49wmkrkofwxbfrs9mmow4udpj7yjpgcsp15qo

  Length: 1
  Channel: dev
```

If you see this output, seeding is active and your app is discoverable.

### Step 4: Share with users

Send your `pear://` link to other users. They run your app with:

```bash
pear run pear://keet4yc8x5dat5n49wmkrkofwxbfrs9mmow4udpj7yjpgcsp15qo
```

Expected output on their machine:

```
ℹ Running: my-chat-app

[App window opens]
```

### Step 5: Update your app (optional)

When you make changes to your app:

1. Stage the new version:

```bash
pear stage dev
```

Output shows incremented length:

```
  Staged 5 files (2.6 KB)
  Length: 2
```

1. Seeding automatically serves the new version. No restart needed.

Peers running your app receive updates automatically if your app handles them:

```javascript
import Pear from 'pear'

Pear.updates(() => {
  console.log('Update available, reloading...')
  Pear.reload()
})
```

## Verification

### Test from another machine

The most reliable way to verify seeding:

1. Go to a different computer (or ask a friend)
1. Run your app by link:

```bash
pear run pear://keet4yc8x5dat5n49wmkrkofwxbfrs9mmow4udpj7yjpgcsp15qo
```

1. If the app opens, seeding works.

### Test from the same machine

If you only have one machine, you can verify the DHT registration:

```bash
pear info pear://keet4yc8x5dat5n49wmkrkofwxbfrs9mmow4udpj7yjpgcsp15qo
```

Expected output:

```
ℹ Info: my-chat-app

  pear://keet4yc8x5dat5n49wmkrkofwxbfrs9mmow4udpj7yjpgcsp15qo

  Length: 1
```

If you see `Length`, the DHT knows about your app.

### Check seeding terminal

While seeding, you may see connection activity:

```
^_^ announced
... peer connected
... peer connected
```

This indicates peers are downloading your app.

## CLI reference

### pear stage

Synchronize local files to the app's Hyperdrive.

```bash
pear stage [channel] [dir]
```

| Option | Description |
|--------|-------------|
| `[channel]` | Channel name: `dev` (default), `production`, or custom |
| `[dir]` | Project directory (defaults to current directory) |
| `--dry-run`, `-d` | Preview changes without writing |
| `--ignore <list>` | Comma-separated paths to ignore |
| `--json` | Output as newline-delimited JSON |

**Examples:**

```bash
# Stage to dev channel
pear stage dev

# Preview what would be staged
pear stage dev --dry-run

# Ignore node_modules and logs
pear stage dev --ignore "node_modules,.git,*.log"

# Stage for production
NODE_ENV=production pear stage dev
```

### pear seed

Make a staged application available on the network.

```bash
pear seed <channel|link> [dir]
```

| Option | Description |
|--------|-------------|
| `<channel>` | Channel name: `dev`, `production` |
| `<link>` | A `pear://` link to reseed (from any machine) |
| `[dir]` | Project directory (defaults to current directory) |

**Examples:**

```bash
# Seed the dev channel (from project directory)
pear seed dev

# Seed the production channel
pear seed production

# Reseed from a link (works on any machine)
pear seed pear://keet4yc8x5dat5n49wmkrkofwxbfrs9mmow4udpj7yjpgcsp15qo
```

### pear info

Display information about an application.

```bash
pear info [channel|link]
```

**Examples:**

```bash
# Show info for dev channel
pear info dev

# Show info for a link
pear info pear://keet4yc8x5dat5n49wmkrkofwxbfrs9mmow4udpj7yjpgcsp15qo
```

### pear release

Mark a staged version as the production release.

```bash
pear release <channel> [dir]
```

**Example workflow:**

```bash
# Stage your tested code
pear stage dev

# Mark current version as release
pear release dev

# Seed the production channel
pear seed production
```

### pear run

Run a Pear application.

```bash
pear run <link|path> [args...]
```

| Option | Description |
|--------|-------------|
| `--checkout=release` | Run the marked release version |
| `--checkout=staged` | Run the latest staged version |
| `--dev` | Enable development mode |

## Troubleshooting

### App not found on network

| Symptom | Cause | Solution |
|---------|-------|----------|
| `pear info` returns nothing | Seeding process not running | Start `pear seed dev` and keep terminal open |
| `pear info` returns nothing | App not staged | Run `pear stage dev` before seeding |
| Peers cannot connect | Firewall blocking | Allow Pear through your firewall |

**Verification:**

```bash
# Check if staging exists
pear info dev
```

If output is empty, stage first:

```bash
pear stage dev
pear seed dev
```

### Seeding stops when terminal closes

| Symptom | Cause | Solution |
|---------|-------|----------|
| Peers lose access when you close laptop | Seeding requires running process | Use a server or keep computer on |

**For production apps**, seed from a server:

```bash
# On your server (via SSH)
pear seed pear://keet4yc8x5dat5n49wmkrkofwxbfrs9mmow4udpj7yjpgcsp15qo
```

Use `tmux` or `screen` to keep the process running after you disconnect:

```bash
# Start a tmux session
tmux new -s pear-seed

# Run seeding
pear seed production

# Detach: press Ctrl+B, then D
# Reattach later: tmux attach -t pear-seed
```

### Peers cannot connect (NAT issues)

| Symptom | Cause | Solution |
|---------|-------|----------|
| Seeding shows `^_^ announced` but peers timeout | Both peers behind strict NAT | One peer needs open network |

**Explanation:** HyperDHT uses "holepunching" to connect peers behind NAT. This fails when both peers use randomizing NATs (common on mobile networks).

**Solutions:**

1. Seed from a server/VPS with public IP
1. Ensure at least one peer is on a home/office network (not mobile)

### Changes not reaching peers

| Symptom | Cause | Solution |
|---------|-------|----------|
| Peers see old version | Forgot to stage | Run `pear stage dev` after changes |
| Peers see old version | App does not handle updates | Add update handling code |

**Add update handling to your app:**

```javascript
import Pear from 'pear'

Pear.updates(() => {
  Pear.reload()
})
```

## Best practices

### Development vs production workflow

**Development:**

```bash
# Quick iteration
pear stage dev
pear seed dev

# Share dev link with testers
```

**Production:**

```bash
# Prepare production build
NODE_ENV=production pear stage dev

# Mark as official release
pear release dev

# Seed production channel
pear seed production

# Share production link with users
```

### Keep apps available 24/7

For production apps, run seeding on infrastructure that stays online:

| Option | Complexity | Cost |
|--------|------------|------|
| Home server | Low | Free |
| VPS (DigitalOcean, etc.) | Medium | $5-10/month |
| Cloud VM (AWS, GCP) | Medium | Varies |

**Example: Seeding on a VPS**

```bash
# SSH into your server
ssh user@your-server.com

# Install Pear
npm install -g pear

# Start seeding in background
tmux new -d -s seeder "pear seed pear://your-app-link"

# Check it is running
tmux ls
```

### When can you stop seeding?

Once other peers run your app, they automatically reseed it. After sufficient peers have your app:

- Casual apps: You can stop seeding; peers keep it alive
- Important apps: Keep at least one seeder running for reliability

**Check peer activity** in the seeding terminal. If you see `peer connected` regularly, your app is being reseeded.

### Optimize app loading

Pear apps load over the network. Reduce initial load time:

| Practice | Why |
|----------|-----|
| Minimize bundle size | Faster first load |
| Lazy-load large assets | Users see UI faster |
| Defer non-critical scripts | Core functionality loads first |
| Avoid autoplay media | Large files load on demand |

## Next steps

| Topic | Link |
|-------|------|
| Building Pear desktop apps | [docs.pears.com/guides/making-a-pear-desktop-app](https://docs.pears.com/guides/making-a-pear-desktop-app) |
| How Hyperswarm works | [docs.pears.com/building-blocks/hyperswarm](https://docs.pears.com/building-blocks/hyperswarm) |
| HyperDHT deep dive | [docs.pears.com/building-blocks/hyperdht](https://docs.pears.com/building-blocks/hyperdht) |
| pear-seed module (programmatic) | [github.com/holepunchto/pear-seed](https://github.com/holepunchto/pear-seed) |
| Sharing apps guide | [docs.pears.com/guide/sharing-a-pear-app](https://docs.pears.com/guide/sharing-a-pear-app) |
