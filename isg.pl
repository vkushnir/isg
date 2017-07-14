#!/usr/bin/perl
# Change subscribed user group according V_ISG view table
use lib "/opt/isg";
use DBI;
use DBD::Oracle;

use Fcntl 'LOCK_EX', 'LOCK_NB';
use strict;
use POSIX qw/strftime/;

use shared;
require "config.pl";
$config::app_log = '/opt/isg/log/isg.log';

# MAIN
_log("ISG::STARTED\n");

# Check if another copy is running
unless ( flock DATA, LOCK_EX | LOCK_NB ) {
    print STDERR "Found duplicate script run. Stopping\n";
    _log("Found duplicate script run. Stopping\n");
    exit(0);
}

$ENV{'NLS_LANG'} = 'RUSSIAN_CIS.UTF8'; 
my $uri = "dbi:$config::db_platform:$config::db_addr/$config::db_name";
my $dbh = DBI->connect($uri, $config::db_user, $config::db_pass) || die("Database connection not made: $DBI::errstr");
   $dbh->{AutoCommit}=1;

my $sth = undef;   
eval {
# Get list of subscribers for group change
   $sth = $dbh->prepare('SELECT * FROM RADIUS.V_ISG WHERE nvl(radgroup,0)!=nvl(new_radgroup,0)') || die "Couldn't prepare statement: " . $dbh->errstr;
   $sth->execute() || die "Couldn't execute statement: " . $sth->errstr;

	# Do group change for list of users
	my @data;
	while (@data = $sth->fetchrow_array()) {
	 
		eval {
		  my $deactivate = "";
		  my $activate  = "";
		  my $session = $data[1];
		  my $service = $data[3];
		  my $new_service = $data[4];
		  my $user = $data[5]; 
		  my $reason = $data[8];
		  my $bras = $data[9];
		  my $service_sky = "SVC_SKY";
		  my $speed = $data[4];
			 $speed =~ s/group_//g;
		  if (!$speed) { $speed = 0; };
	 
		  # Change group in database
		  my $sql =	"DECLARE\n" .
					" out_code number;\n" .
					" out_message varchar2(256);\n" .
					"BEGIN\n" .
					"  radius.change_user_speed('$user', '$speed', $reason, out_code, out_message);\n" .
					"END;";
				
			my $sth = $dbh->prepare($sql)|| die "Couldn't prepare statement: ". $dbh->errstr;
			$sth->execute() || die "Couldn't execute statement: ". $sth->errstr;
			# If subscriber online, try to change service to new one
			if ($session) {
				$new_service =~ s/group/SVC/g;
				$service =~ s/group/SVC/g;		
				# Deactivate active service
				cmd("deactivate-service", $bras, $user, $session, $service);
				cmd("deactivate-service", $bras, $user, $session, $service_sky);
		
				cmd("activate-service", $bras, $user, $session, $new_service);
				cmd("activate-service", $bras, $user, $session, $service_sky);			
			};
		};
		if ($@) { print("     Update block error: $@"); };
	};		
};
if ($@) { 
	print("     Update block error: $@");	
};

# FINISH
if (defined $sth) {$sth->finish;}
$dbh->disconnect;
_log("ISG::STOPPED");

### DO NOT REMOVE THE FOLLOWING LINES ###

__DATA__
This exists to allow the locking code at the beginning of the file to work.
DO NOT REMOVE THESE LINES!
