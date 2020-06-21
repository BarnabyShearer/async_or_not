.PRECIOUS: output-%

output-%: %.json
	-rm -Rf $@
	packer build $+

output-%: app.json %/* output-ubuntu
	-rm -Rf $@
	packer build -var "service=$*" app.json

%/demo: %/main.go
	cd $*; go build .

output-golang: golang/demo

%: output-% output-postgresql
	# Reset to empty DB
	-rm output-postgresql/data
	qemu-img create -f qcow2 -b packer-postgresql output-postgresql/data
	# Run Postgres VM
	(qemu-system-x86_64 \
        -machine type=pc,accel=kvm \
        -m 1024M \
        -device virtio-net,netdev=user.0 \
        -netdev user,id=user.0,hostfwd=tcp::5678-:5432 \
        -drive file=output-postgresql/data,if=virtio,cache=writeback,discard=ignore,format=qcow2 \
        -vnc :0 & echo $$! > .postgres.pid)
	sleep 5
	# Run App VM
	(qemu-system-x86_64 \
        -machine type=pc,accel=kvm \
        -m 1024M \
        -device virtio-net,netdev=user.0 \
        -netdev user,id=user.0,hostfwd=tcp::8880-:80 \
        -drive file=output-$*/packer-$*,if=virtio,cache=writeback,discard=ignore,format=qcow2 \
        -vnc :1 & echo $$! > .app.pid)
	sleep 5
    # Warm
	ab -n 100 -c 25 -p payload.json http://localhost:8880/ > /dev/null
	sleep 2
	@echo ======= $* =======
	ab -n 10000 -c 25 -p payload.json http://localhost:8880/
    # Cleanup
	kill `cat .app.pid`
	kill `cat .postgres.pid`
