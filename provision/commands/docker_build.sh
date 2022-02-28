docker image build -t test_project_template-development:latest \
	--target builder \
	--build-arg USER_ID=1000 \
	--build-arg GROUP_ID=1000 \
	--build-arg USERNAME=lgblkb \
	--build-arg PROJECT_DIR=/home/lgblkb/PycharmProjects/project_template /home/lgblkb/PycharmProjects/project_template "$@"