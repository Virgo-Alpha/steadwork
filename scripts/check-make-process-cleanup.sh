#!/bin/sh
set -eu

root_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
check_dir="$root_dir/.steadwork-process-check"
bin_dir="$check_dir/bin"
mkdir -p "$bin_dir"
cleanup() {
	[ -n "${dev_pid:-}" ] && kill "$dev_pid" 2>/dev/null || true
	rm -rf "$check_dir"
}
trap cleanup EXIT INT TERM

cat >"$bin_dir/npm" <<'EOF'
#!/bin/sh
sleep 300 &
echo "$!" >"$CHECK_DIR/frontend-child.pid"
wait "$!"
EOF
cat >"$bin_dir/uv" <<'EOF'
#!/bin/sh
sleep 300 &
echo "$!" >"$CHECK_DIR/backend-child.pid"
wait "$!"
EOF
chmod +x "$bin_dir/npm" "$bin_dir/uv"

CHECK_DIR="$check_dir" PATH="$bin_dir:$PATH" make -C "$root_dir" dev >"$check_dir/dev.log" 2>&1 &
dev_pid=$!
for file in frontend-child.pid backend-child.pid; do
	for _ in 1 2 3 4 5 6 7 8 9 10; do
		[ -f "$check_dir/$file" ] && break
		sleep 1
	done
	test -f "$check_dir/$file"
done

kill -TERM "$dev_pid"
wait "$dev_pid" || true
for file in frontend-child.pid backend-child.pid; do
	child_pid=$(cat "$check_dir/$file")
	if kill -0 "$child_pid" 2>/dev/null; then
		printf '%s\n' "nested process survived cleanup: $child_pid" >&2
		exit 1
	fi
done
printf '%s\n' "process-group cleanup passed"
