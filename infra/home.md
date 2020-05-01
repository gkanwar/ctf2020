## WTF?
CTF! Capture Tej's Flags! Capture flags (secret strings) from your opponents' servers. Protect your own.


## What is a flag?
Strings that look like, for example, `FLAG_VbDgYwwNs6w3AwAAAABEFEtvyHhdDRuN`. Specifically, flags will always be of the form `FLAG_<base64-encoded-data>` and will therefore match the regex `^FLAG_[a-zA-Z0-9+/]*={0,3}$`.

Flags represent private data that users have on your server. Protect them!


## How do I access my server?
Everything will be hooked up using OpenVPN. Use the provided config file to connect your machine to the game network:

  * **OSX:** Install Tunnelblick, `open teamX_Y.conf`
  * **Ubuntu:** `sudo apt install openvpn && sudo openvpn --config /path/to/teamX_Y.conf`
  * **Other linux flavors:** Somehow install OpenVPN, `sudo openvpn --config /path/to/teamX_Y.conf`
  * **Windows:** Rethink life choices? (But actually, I have no idea; let me know if you figure it out)

Everyone on your team should use a unique conf file to connect.

From there you can SSH into your server (`10.10.X.1`, X= team #) using the provided user/pass. Save some time by [adding your public key](https://www.debian.org/devel/passwordlessssh) to `${HOME}/.ssh/authorized_keys`.


## How do I access other servers?
They live at the corresponding IPs, `10.10.X.1` (X = team #). Your requests go through Network Address Translation, so should look just like any other team and the checker scripts (i.e. you cannot just block other team's IPs).

Team 66 is a "NOP" team. They sit there and get hacked. Their flags are not worth points, but you can check exploits against them, since other teams might have started patching / modifying their servers.


## How do I submit flags?
Good job stealing a flag! Now doff your black hat and make sure you report this stolen data to the appropriate authorities. Pipe flags, one per line, into `nc 10.10.10.10 31337`. Per line you will receive a response indicating whether the flag was accepted or why it was not:

- `OK you received <N> pts for reporting this data leak!`
- `ERR invalid flag format`
- `ERR unknown flag`
- `ERR flag too old`
- `ERR your own flag`
- `ERR flag already submitted`
- `ERR flag from NOP team`
- `ERR internal error`
- `ERR game not running`


## I want points?
Oh, and financial stability, satisfaction at work and in life too? Well I can give you points at least. The game is based around a tick system: every 5 minutes the users (checker scripts) will go around and use your service, store flags, and ensure they can still retrieve them. There are `M` types of flags corresponding to different places where users put their private data (**Value of `M` TBD**). Maintaining a service level agreement (SLA), i.e. ensuring your service is usable by the checking users, is worth 100 points per type of flag = 100`M` points per tick.

Meanwhile, you should try to steal other teams' flags and protect your own. Every stolen flag is worth a dynamic number of points `P`,

    P = 500 / (A + 5)
    A = # flags of this type you have stolen from this team before this one

Unpacking the math: the first flag is worth 100 points and you quickly see diminishing returns from repeatedly stealing the same type of flag from the same team. In the limit of infinite rounds you could grow your points arbitrarily, since sum_x(1/x) = infinity, but there are finitely many rounds so invest your time wisely.

Losing private data is a **big deal** and your users will start asking some hard questions whenever you lose their data! Every type of flag you lose takes up to 50 points away from the SLA points you would have gotten. For example, if your service is fully functional, but you lost a flag you only get 50 SLA points instead of 100 that round.


## I can has srzcode?
Yup! Take a look at `/tasks`. Your service is running inside a Docker container, and it's (mostly<sup>*</sup>) Python so dig away.

<sup>*</sup>I had to write some HTML/JS/CSS to make this thing look presentable, sorry. Only Python runs server-side and therefore it will have all the logic and vulnerabilities!

### Docker
Handy Docker cheatsheet: [https://devhints.io/docker-compose](https://devhints.io/docker-compose). When you modify your server code you will need to run something like

    # optionally also pass -d to daemonize and return control to bash
    docker-compose -f /path/to/docker-compose.yml up --build

to ensure the docker container is refreshed. You may also find it handy to check logs from your service (e.g. if you are print debugging) via

    docker container ls # find hexadecimal container id
    docker logs <container id>


## I found a way to totally pwn another server?
Woah, awesome. But if "totally pwn" includes (1) overwriting source code, (2) deleting flag info, or (3) overloading the machine (DoS'ing), **please do not**. These sorts of bugs are unintentional and means Tej fucked up. Let me know instead!

Your machine is set up to allow my "god key" access. I'll patch these things on the fly if it seems simple to do so.


## I am stuck. Halp.
Message me somehow (Discord preferred) and I'll happily drop some hints. I want everyone to be making progress and having [Fun](https://dwarffortresswiki.org/index.php?title=DF2014:Fun&redirect=yes), ... err ... fun!

A few generally-useful resources:
**COMING SOON**
