#!/usr/bin/perl

use lib "/opt/isg";
use DBI;
use DBD::Oracle;
use strict;

use shared;
require "config.pl";

_log("ISG TERMINATOR::STARTED");

# Connect to database
$ENV{'NLS_LANG'} = 'RUSSIAN_CIS.UTF8'; 
my $uri = "dbi:$config::db_platform:$config::db_addr/$config::db_name";
my $dbh = DBI->connect($uri, $config::db_user, $config::db_pass) || die("Database connection not made: $DBI::errstr");
   $dbh->{AutoCommit}=1;
   
my $sth = undef;   
eval {
	$sth = $dbh->prepare("SELECT * FROM RADIUS.V_ISG WHERE sessionid is not null") || die "Couldn't prepare statement: " . $dbh->errstr;
	$sth->execute() || die "Couldn't execute statement: " . $sth->errstr;   

	# Do group change for list of users
	my @data;
	while (@data = $sth->fetchrow_array()) {
		eval {		
			my $session = $data[1];
			my $service = $data[3];
			my $user = $data[5];  			
			my $bras =  $data[9];
			
			$service =~ s/group/SVC/g;
			my $service_sky = "SVC_SKY";
			my $service_kz = "SVC_KZ";		
			
			cmd("deactivate-service", $bras, $user, $session, $service);
			cmd("deactivate-service", $bras, $user, $session, $service_kz);
			cmd("deactivate-service", $bras, $user, $session, $service_sky);
			
			cmd("activate-service", $bras, $user, $session, $service);
			cmd("activate-service", $bras, $user, $session, $service_kz);
			cmd("activate-service", $bras, $user, $session, $service_sky);			
			
		};
		if ($@) { print("Update block error: $@"); };
		
	};

};
if ($@) { 
	print("Update block error: $@"); 
};

# FINISH
if (defined $sth) {$sth->finish;}
$dbh->disconnect;
_log("ISG TERMINATOR::STOPPED");


