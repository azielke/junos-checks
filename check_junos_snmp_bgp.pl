#!/usr/bin/perl
use strict;
use warnings;

use Getopt::Long;
use Net::SNMP;
use Net::IP;
use Data::Dumper;

my %bgpPeerStatesText = (
    1 => "idle",
    2 => "connect",
    3 => "active",
    4 => "opensent",
    5 => "openconfirm",
    6 => "established",
);

my $router;
my $snmp_community = "public";
my $local_address;
my $peer_address;
my $afi;
my $v4 = 1;
my $v6 = 0;

GetOptions (
    "router=s"    => \$router,
    "community=s" => \$snmp_community,
    "local=s"     => \$local_address,
    "peer=s"      => \$peer_address,
    "4"           => \$v4,
    "6"           => \$v6,
) or die("Error in command line arguments\n");

my $local = Net::IP->new($local_address);
my $peer  = Net::IP->new($peer_address);

my $local_oid;
my $peer_oid;

if ( $v6 ) {
    $afi = 2;
    if ( $local->version != 6 ) {
        print "local not IPv6\n";
        exit 3;
    }
    if ( $local->version != 6 ) {
        print "peer not IPv6\n";
        exit 3;
    }

    $local_oid = join '.', unpack("C"x16, pack("B128", $local->binip));
    $peer_oid  = join '.', unpack("C"x16, pack("B128", $peer->binip));
} elsif ( $v4 ) {
    $afi = 1;
    if ( $local->version != 4 ) {
        print "local not IPv4\n";
        exit 3;
    }
    if ( $local->version != 4 ) {
        print "peer not IPv4\n";
        exit 3;
    }

    $local_oid = $local->ip;
    $peer_oid  = $peer->ip;
}

##### Prepare OIDs
my $oid = "$afi.$local_oid.$afi.$peer_oid";

my $jnxBgpM2Peer                 = ".1.3.6.1.4.1.2636.5.1.1.2";
my $jnxBpgM2PeerEntry            = "$jnxBgpM2Peer.1.1.1";
my $jnxBgpM2PrefixCountersEntry  = "$jnxBgpM2Peer.6.2.1";

my $jnxBgpM2PeerState            = "$jnxBpgM2PeerEntry.2";
my $jnxBgpM2PeerIndex            = "$jnxBpgM2PeerEntry.14";

my $peerState_oid = "$jnxBgpM2PeerState.0.$oid";
my $peerIndex_oid = "$jnxBgpM2PeerIndex.0.$oid";

my ($session, $error) = Net::SNMP->session(
    -hostname  => $router,
    -community => $snmp_community,
);

if (!defined $session) {
    printf "BGP UNKNOWN: %s.\n", $error;
    exit 3;
}


##### Collect State
my $result = $session->get_request(-varbindlist => [
    $peerState_oid, $peerIndex_oid
]);

if (!defined $result) {
    if ( $session->error_status() == 2 ) {
        printf "BGP UNKNOWN: No BGP Session from %s to %s\n", $local->short ,$peer->short;
        exit 3;
    }
    print Dumper($session->error_status());
    printf "ERROR: %s.\n", $session->error();
    $session->close();
    exit 3;
}

my $peerState = $result->{$peerState_oid};
my $peerIndex = $result->{$peerIndex_oid};


##### Collect Performance Data
my $inPrefixes;
my $inPrefixesAccepted;
my $inPrefixesRejected;
my $outPrefixes;
my $inPrefixesActive;

if ( $peerState == 6 ) {
    my $jnxBgpM2PrefixInPrefixes           = "$jnxBgpM2PrefixCountersEntry.7.$peerIndex.$afi.1";
    my $jnxBgpM2PrefixInPrefixesAccepted   = "$jnxBgpM2PrefixCountersEntry.8.$peerIndex.$afi.1";
    my $jnxBgpM2PrefixInPrefixesRejected   = "$jnxBgpM2PrefixCountersEntry.9.$peerIndex.$afi.1";
    my $jnxBgpM2PrefixOutPrefixes          = "$jnxBgpM2PrefixCountersEntry.10.$peerIndex.$afi.1";
    my $jnxBgpM2PrefixInPrefixesActive     = "$jnxBgpM2PrefixCountersEntry.11.$peerIndex.$afi.1";


    $result = $session->get_request(-varbindlist => [
        $jnxBgpM2PrefixInPrefixes,
        $jnxBgpM2PrefixInPrefixesAccepted,
        $jnxBgpM2PrefixInPrefixesRejected,
        $jnxBgpM2PrefixOutPrefixes,
        $jnxBgpM2PrefixInPrefixesActive,
    ]);

    if (!defined $result) {
        printf "ERROR: %s.\n", $session->error();
        $session->close();
        exit 3;
    }

    $inPrefixes = $result->{$jnxBgpM2PrefixInPrefixes};
    $inPrefixesAccepted = $result->{$jnxBgpM2PrefixInPrefixesAccepted};
    $inPrefixesRejected = $result->{$jnxBgpM2PrefixInPrefixesRejected};
    $outPrefixes = $result->{$jnxBgpM2PrefixOutPrefixes};
    $inPrefixesActive = $result->{$jnxBgpM2PrefixInPrefixesActive};
} else {
    $inPrefixes = 0;
    $inPrefixesAccepted = 0;
    $inPrefixesRejected = 0;
    $outPrefixes = 0;
    $inPrefixesActive = 0
}
$session->close();


##### Output Status and Performance Data
my $rc = 0;
my $state = "OK";
if ( $peerState != 6 ) {
    $state = "CRITICAL";
    $rc = 2;
}
printf "BGP %s: %s", $state, $bgpPeerStatesText{$peerState};
print "|inPrefixes=$inPrefixes";
print " inPrefixesAccepted=$inPrefixesAccepted";
print " inPrefixesRejected=$inPrefixesRejected";
print " outPrefixes=$outPrefixes";
print " inPrefixesActive=$inPrefixesActive";
print "\n";
exit $rc;
