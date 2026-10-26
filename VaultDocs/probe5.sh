#!/bin/bash
echo "=== id ==="; id
echo "=== root.txt ==="; cat /root/root.txt
echo "=== host-side mounts contents ==="
for d in /var/lib/kubelet /var/lib/k0s /var/lib/rancher/k3s /var/lib/rancher/rke2 /var/lib/containerd /var/lib/buildkit /run; do
  echo "--- $d ---"; ls -la "$d" 2>&1 | head -8
done
echo "=== /run ==="; ls -la /run 2>/dev/null | head -30
echo "=== whoami direct ==="; whoami
