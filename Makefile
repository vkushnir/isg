DESTDIR   ?=
prefix    ?= /opt/isg
bindir    ?= $(prefix)
confdir   ?= $(prefix)
libdir    ?= $(prefix)
logdir    ?= $(prefix)/log
conffile  ?= config.pl

logrotate ?= /etc/logrotate.d

INSTALL         := install
INSTALL_DATA    := $(INSTALL) -m 644
INSTALL_DIR     := $(INSTALL) -m 755 -d
INSTALL_PROGRAM := $(INSTALL) -m 755

install-config: $(conffile)-sample
	$(INSTALL_DIR) $(DESTDIR)$(confdir)
	@if [ -f $(DESTDIR)$(confdir)/$(conffile) ]; then \
		echo -e "****       \e[00;31m$(conffile) already exists.\e[00m Skip copying.        ****"; \
	else \
	  $(INSTALL_DATA) $(conffile)-sample $(DESTDIR)$(confdir)/$(conffile); \
	fi

install-bin: isg.pl isg_reactivate.pl
	$(INSTALL_DIR) $(DESTDIR)$(bindir)
	$(INSTALL_PROGRAM) $^ $(DESTDIR)$(bindir)
	
install-lib: shared.pm
	$(INSTALL_DIR) $(DESTDIR)$(libdir)
	$(INSTALL_DATA) $^ $(DESTDIR)$(libdir)
	
install-log: isg.logrotate
	$(INSTALL_DIR) $(DESTDIR)$(logdir)
	$(INSTALL_DATA) isg.logrotate $(logrotate)/isg

install: install-lib install-bin install-log install-config	