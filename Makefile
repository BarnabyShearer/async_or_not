.PHONY: all sync async postgres benchmark

all: output-postgresql/packer-postgresql output-sync/packer-sync output-async/packer-async

output-ubuntu/packer-ubuntu: ubuntu.json
	-rm -Rf output-ubuntu
	packer build ubuntu.json

output-postgresql/packer-postgresql: postgres.json output-ubuntu/packer-ubuntu
	-rm -Rf output-postgresql
	packer build postgres.json

output-sync/packer-sync: app.json sync/* output-ubuntu/packer-ubuntu
	-rm -Rf output-sync
	packer build -var "service=sync" app.json

output-async/packer-async: app.json async/* output-ubuntu/packer-ubuntu
	-rm -Rf output-async
	packer build -var "service=async" app.json

postgres: output-postgresql/packer-postgresql
	qemu-system-x86_64 \
        -machine type=pc,accel=kvm \
        -m 1024M \
        -device virtio-net,netdev=user.0 \
        -netdev user,id=user.0,hostfwd=tcp::5678-:5432 \
        -drive file=output-postgresql/packer-postgresql,if=virtio,cache=writeback,discard=ignore,format=qcow2 \
        -vnc :0

sync: output-sync/packer-sync
	qemu-system-x86_64 \
        -machine type=pc,accel=kvm \
        -m 1024M \
        -device virtio-net,netdev=user.0 \
        -netdev user,id=user.0,hostfwd=tcp::8881-:80 \
        -drive file=output-sync/packer-sync,if=virtio,cache=writeback,discard=ignore,format=qcow2 \
        -vnc :1

async: output-async/packer-async
	qemu-system-x86_64 \
        -machine type=pc,accel=kvm \
        -m 1024M \
        -device virtio-net,netdev=user.0 \
        -netdev user,id=user.0,hostfwd=tcp::8882-:80 \
        -drive file=output-async/packer-async,if=virtio,cache=writeback,discard=ignore,format=qcow2 \
        -vnc :2

benchmark:
	ab -n 100 -c 25 -p payload.json http://localhost:8881/ > /dev/null
	ab -n 100 -c 25 -p payload.json http://localhost:8882/ > /dev/null
	sleep 2
	ab -n 10000 -c 25 -p payload.json http://localhost:8881/
	sleep 2
	ab -n 10000 -c 25 -p payload.json http://localhost:8882/
