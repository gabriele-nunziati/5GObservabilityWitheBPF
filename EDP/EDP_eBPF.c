#include <uapi/linux/ptrace.h>
#include <net/sock.h>
#include <bcc/proto.h>


#define IP_UDP 17
#define ETH_HLEN 14

//Definition of the Hash Map
BPF_HASH(last);

int pfcp_filter(struct __sk_buff *skb) {

	//Definition for delta
	u64 ts, *tsp, delta, key, detected = 0;

	u8 *cursor = 0;

	struct ethernet_t *ethernet = cursor_advance(cursor, sizeof(*ethernet));
	//filter IP packets (ethernet type = 0x0800)
	if (!(ethernet->type == 0x0800)) {
		goto DROP;
	}

	struct ip_t *ip = cursor_advance(cursor, sizeof(*ip));

	//filter UDP packets
	if (ip->nextp != IP_UDP) {
		goto DROP;
	}

  u32 udp_header_length = 0;

	u32  ip_header_length = 0;
	u32  payload_offset = 0;
	u32  payload_length = 0;

	//calculate ip header length
	//value to multiply * 4
	//e.g. ip->hlen = 5 ; IP Header Length = 5 x 4 byte = 20 byte
	ip_header_length = ip->hlen << 2;

  //check ip header length against minimum
	if (ip_header_length < sizeof(*ip)) {
		goto DROP;
	}

  //shift cursor forward for dynamic ip header size
  void *_ = cursor_advance(cursor, (ip_header_length-sizeof(*ip)));

  //struct tcp_t *tcp = cursor_advance(cursor, sizeof(*tcp));
  struct udp_t *udp = cursor_advance(cursor, sizeof(*udp));

	//FILTER UDP PACKETS THAT DON'T HAVE 8805 AS BOTH PORTS AND WHOSE LENGTH IS NOT 24
	//only udp from 8805 port to 8805 port whose length is 24
	if( udp->sport == 8805 && udp->dport == 8805 && udp->length == 24) {
		; //continue
	} else {
		goto DROP;
	}

	//LOAD BYTE WHOSE OFFSET IS 43.
	//42th TO PUT AT THE byte0 of PFCP PACKET
	//43th TO LOAD byt1 of PFCP PACKET that contains Message_type

	unsigned long verflag;
	u32 offs = 42 + 1;
	verflag = load_byte(skb, offs);

	if (verflag == 54) {
		//SESSION DELETION REQUEST CASE
		tsp=NULL;
		key=0;

		tsp = last.lookup(&key);
		if (tsp != NULL) {
			delta = bpf_ktime_get_ns() - *tsp;
					//If delta < 1 second, packet to be detected, otherwise discarded
					if (delta < 1000000000) {
						//output if time is less than 1 second
						//bpf_trace_printk("%d\\n", delta / 1000000);
						detected = 1;
					}
					else {
						//delta is greater than 1 second
						detected = 0;
					}

			last.delete(&key);
 		}

		//update stored timestamp
    ts = bpf_ktime_get_ns();
    last.update(&key, &ts);

		//if is to be detected, keep it, otherwise drop it
		if(detected == 1)
			goto KEEP;
		else
			goto DROP;

	} else {
		goto DROP;
	}

	//no match
	goto DROP;

	//keep the packet and send it to userspace returning -1
	KEEP:
	return -1;

	//drop the packet returning 0
	DROP:
	return 0;

}
