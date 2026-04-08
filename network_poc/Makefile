CC = gcc
CFLAGS = -Wall -Wextra

all: client p2p_node

client: client.c
	$(CC) $(CFLAGS) -o client client.c

p2p_node: p2p_node.c
	$(CC) $(CFLAGS) -o p2p_node p2p_node.c

clean:
	rm -f client p2p_node
