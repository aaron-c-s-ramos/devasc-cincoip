# CincoIP backlog

This list contains the enhancements that the team did not include in version 1.0.0. The team will use this backlog in Project Activity 4.

The priority shows the value for a network technician. The size is a team estimate: S = less than 2 hours, M = 2 to 6 hours, L = more than 6 hours.

| ID | Enhancement | Value | Priority | Size |
|---|---|---|---|---|
| B-01 | Automatic test run on each pull request (GitHub Actions). | The team finds a defect before the merge. | High | S |
| B-02 | Local addresses and NAT detection. Show the private IPv4 and IPv6 addresses of the computer and compare them with the public addresses. | The technician sees if the computer is behind NAT or CGNAT. | High | M |
| B-03 | Bulk lookup. Read a list of addresses from a file (`--file addresses.txt`). | The technician examines many addresses with one command. | High | M |
| B-04 | Reverse DNS. Show the host name (PTR record) of each address. | The technician identifies the owner of an address more quickly. | Medium | S |
| B-05 | Interactive menu. Show a menu when the user starts the application without options. | New users do not have to learn the options. | Medium | M |
| B-06 | Cache. Keep the result of a lookup for a short time. | The application uses less of the API quota. | Medium | M |
| B-07 | Monitor mode. Examine the public address at an interval and tell the user when the address changes. | The technician finds a change of a dynamic address. | Medium | M |
| B-08 | Container image (Docker). | The application runs the same on each computer. | Medium | S |
| B-09 | API key support. Read an optional key from an environment variable for paid API plans. | The application gets a larger quota. | Low | S |
| B-10 | Map link. Show an OpenStreetMap link for the coordinates. | The technician sees the location on a map. | Low | S |
| B-11 | Subnet calculator. Show the network address, the broadcast address, and the host range for an address and a prefix. | The technician uses one tool for more tasks. | Low | M |
| B-12 | Web interface (Flask). | Users without a terminal can use the application. | Low | L |

## Rules for the backlog

1. Add a new item at the end of the table with the next ID.
2. Do not delete a completed item. Move it to a "Completed" table with the version number.
3. Make one branch and one pull request for each item.
